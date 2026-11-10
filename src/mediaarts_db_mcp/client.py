import json
import re
from typing import Annotated, Any, Literal

import httpx
from pydantic import Field, validate_call

API_URL = "https://mediaarts-db.artmuseums.go.jp/sparql"
ITEM_URL = "https://mediaarts-db.artmuseums.go.jp/id/"
IssueId = Annotated[str, Field(pattern=r"^M[0-9]{1,20}$")]
SearchText = Annotated[str, Field(min_length=1, max_length=100, pattern=r"\S")]
IssueNumber = Annotated[str, Field(min_length=1, max_length=40, pattern=r"\S")]
Year = Annotated[int, Field(ge=1000, le=9999)]
Medium = Literal["manga", "anime", "game"]
Limit = Annotated[int, Field(ge=1, le=50)]
Start = Annotated[int, Field(ge=1, le=10001)]

PREFIXES = """
PREFIX schema: <https://schema.org/>
PREFIX class: <https://mediaarts-db.artmuseums.go.jp/data/class#>
PREFIX ma: <https://mediaarts-db.artmuseums.go.jp/data/property#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""
WORK_CLASSES = {
    "manga": ("MangaBookSeries", "MangaMagazinePublication"),
    "anime": ("AnimationTVRegularSeries", "AnimationTVSpecialSeries", "AnimationMovieSeries"),
    "game": ("GameWork",),
}


async def _query_rows(query: str, limit: int) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.get(
                API_URL,
                params={"query": query},
                headers={"Accept": "application/sparql-results+json"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"MADB returned HTTP {exc.response.status_code}.") from None
        except httpx.RequestError:
            raise ValueError("MADB could not be reached. Retry later.") from None

    try:
        rows = response.json()["results"]["bindings"]
        if not isinstance(rows, list) or len(rows) > limit + 1:
            raise ValueError
        return rows
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ValueError("MADB returned unexpected SPARQL results.") from None


def _next_start(rows: list[dict[str, Any]], limit: int, start: int) -> int | None:
    return start + limit if len(rows) > limit and start + limit <= 10001 else None


def _record_id(url: str, prefix: str) -> str:
    match = re.fullmatch(rf"{re.escape(ITEM_URL)}({prefix}[0-9]{{1,20}})", url)
    if match is None:
        raise ValueError("MADB returned an unexpected record ID.")
    return match[1]


@validate_call
async def get_manga_issue_contents(
    issue_id: IssueId, limit: Limit = 20, start: Start = 1
) -> dict[str, Any]:
    """List works and start pages in a manga magazine issue by its MADB ID."""
    query = f"""
PREFIX schema: <https://schema.org/>
PREFIX class: <https://mediaarts-db.artmuseums.go.jp/data/class#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?title ?work ?page ?kind WHERE {{
    <{ITEM_URL}{issue_id}> a class:MangaMagazineIssue ;
        schema:hasPart ?part .
    ?part schema:pageStart ?page .
    OPTIONAL {{ ?part schema:alternativeHeadline ?title . }}
    OPTIONAL {{ ?part schema:name ?work . }}
    FILTER(BOUND(?title) || BOUND(?work))
    OPTIONAL {{ ?part schema:genre ?kind . }}
}}
ORDER BY xsd:decimal(?page) ?page ?title ?work ?kind
LIMIT {limit + 1}
OFFSET {start - 1}
"""
    rows = await _query_rows(query, limit)
    try:
        items = [
            {
                "title": row.get("title", {}).get("value"),
                "work_title": row.get("work", {}).get("value"),
                "start_page": row["page"]["value"],
                "category": row.get("kind", {}).get("value"),
            }
            for row in rows[:limit]
        ]
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ValueError("MADB returned unexpected SPARQL results.") from None
    return {
        "issue_id": issue_id,
        "source_url": ITEM_URL + issue_id,
        "items": items,
        "next_start": _next_start(rows, limit, start),
    }


@validate_call
async def search_manga_issues(
    query: SearchText,
    volume_number: IssueNumber | None = None,
    issue_number: IssueNumber | None = None,
    year: Year | None = None,
    limit: Limit = 20,
    start: Start = 1,
) -> dict[str, Any]:
    """Find manga magazine issue IDs by title, optionally narrowed by volume, issue or year."""
    query_literal = json.dumps(query.strip(), ensure_ascii=False)
    filters = [f"FILTER(CONTAINS(LCASE(STR(?label)), LCASE({query_literal})))"]
    if volume_number is not None:
        filters.append(
            f"FILTER(STR(?volumeValue) = {json.dumps(volume_number.strip(), ensure_ascii=False)})"
        )
    if issue_number is not None:
        filters.append(
            f"FILTER(STR(?numberValue) = {json.dumps(issue_number.strip(), ensure_ascii=False)})"
        )
    if year is not None:
        filters.append(
            f'FILTER(STR(?yearValue) = "{year}" || STRSTARTS(STR(?dateValue), "{year}-"))'
        )
    sparql = f"""{PREFIXES}
SELECT ?record (MIN(STR(?label)) AS ?title) (MIN(STR(?volumeValue)) AS ?volume)
       (MIN(STR(?numberValue)) AS ?issue) (MIN(STR(?dateValue)) AS ?published)
WHERE {{
    ?record a class:MangaMagazineIssue ; rdfs:label ?label .
    OPTIONAL {{ ?record schema:volumeNumber ?volumeValue . }}
    OPTIONAL {{ ?record ma:issueNumberDisplayed ?displayed . }}
    OPTIONAL {{ ?record schema:issueNumber ?catalogNumber . }}
    BIND(COALESCE(?displayed, ?catalogNumber) AS ?numberValue)
    OPTIONAL {{ ?record schema:datePublished ?dateValue . }}
    OPTIONAL {{ ?record ma:yearDisplayed ?yearValue . }}
    {" ".join(filters)}
}}
GROUP BY ?record
ORDER BY DESC(?published) ?record
LIMIT {limit + 1}
OFFSET {start - 1}
"""
    rows = await _query_rows(sparql, limit)
    try:
        items = [
            {
                "issue_id": _record_id(row["record"]["value"], "M"),
                "title": row["title"]["value"],
                "volume_number": row.get("volume", {}).get("value") or None,
                "issue_number": row.get("issue", {}).get("value") or None,
                "published_date": row.get("published", {}).get("value") or None,
                "source_url": row["record"]["value"],
            }
            for row in rows[:limit]
        ]
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ValueError("MADB returned unexpected SPARQL results.") from None
    return {"items": items, "next_start": _next_start(rows, limit, start)}


@validate_call
async def search_works(
    query: SearchText, medium: Medium, limit: Limit = 20, start: Start = 1
) -> dict[str, Any]:
    """Search work and series titles in the selected manga, anime or game catalog."""
    classes = " ".join(f"class:{name}" for name in WORK_CLASSES[medium])
    sparql = f"""{PREFIXES}
SELECT ?record ?type (MIN(STR(?label)) AS ?title)
WHERE {{
    VALUES ?type {{ {classes} }}
    ?record a ?type ; rdfs:label ?label .
    FILTER(CONTAINS(LCASE(STR(?label)), LCASE({json.dumps(query.strip(), ensure_ascii=False)})))
}}
GROUP BY ?record ?type
ORDER BY ?title ?record ?type
LIMIT {limit + 1}
OFFSET {start - 1}
"""
    rows = await _query_rows(sparql, limit)
    try:
        items = [
            {
                "work_id": _record_id(row["record"]["value"], "C"),
                "title": row["title"]["value"],
                "category": row["type"]["value"].rsplit("#", 1)[-1],
                "source_url": row["record"]["value"],
            }
            for row in rows[:limit]
        ]
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ValueError("MADB returned unexpected SPARQL results.") from None
    return {"medium": medium, "items": items, "next_start": _next_start(rows, limit, start)}
