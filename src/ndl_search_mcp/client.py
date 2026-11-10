from __future__ import annotations

import re
from typing import Annotated, Any
from xml.etree import ElementTree

import httpx
from pydantic import Field, validate_call

BASE_URL = "https://ndlsearch.ndl.go.jp/api/"
Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=100)]
ISBN = Annotated[str, Field(min_length=10, max_length=32, pattern=r"^[0-9Xx -]+$")]
NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "opensearch": "http://a9.com/-/spec/opensearchrss/1.0/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}


async def get_response(path: str, **params: str | int | None) -> httpx.Response:
    query = {key: value for key, value in params.items() if value is not None}
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
            response = await client.get(path, params=query)
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"Upstream HTTP error {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise ValueError("Could not reach the upstream API.") from exc


def digitized_pids(item: ElementTree.Element) -> list[str]:
    pids: dict[str, None] = {}
    for identifier in item.findall("dc:identifier", NAMESPACES):
        if match := re.fullmatch(r"info:ndljp/pid/([0-9]{1,20})", (identifier.text or "").strip()):
            pids[match[1]] = None
    for link in item.findall("rdfs:seeAlso", NAMESPACES):
        url = link.get(f"{{{NAMESPACES['rdf']}}}resource", "")
        if match := re.fullmatch(r"https?://dl\.ndl\.go\.jp/pid/([0-9]{1,20})/?", url):
            pids[match[1]] = None
    return list(pids)


@validate_call
async def search_bibliography(
    title: Query | None = None,
    creator: Query | None = None,
    limit: Limit = 10,
    start: Annotated[int, Field(ge=1, le=10001)] = 1,
    isbn: ISBN | None = None,
) -> dict[str, Any]:
    """Search by title, author, or ISBN. Use digitized_pids for IIIF. Start is one-based."""
    if isbn is not None:
        isbn = isbn.replace("-", "").replace(" ", "").upper()
        if not re.fullmatch(r"[0-9]{9}[0-9X]|97[89][0-9]{10}", isbn):
            raise ValueError("Provide an ISBN-10 or ISBN-13.")
    if not title and not creator and not isbn:
        raise ValueError("Provide a title, creator, or ISBN.")
    response = await get_response(
        "opensearch", title=title, creator=creator, cnt=limit, idx=start, isbn=isbn
    )
    xml = response.content.decode("utf-8-sig")
    if "<!DOCTYPE" in xml:
        raise ValueError("Unexpected DTD in the NDL Search response.")
    channel = ElementTree.fromstring(xml).find("channel")
    if channel is None:
        raise ValueError("The NDL Search API did not return an RSS channel.")
    return {
        "total": int(channel.findtext("opensearch:totalResults", "0", NAMESPACES)),
        "start": start,
        "records": [
            {
                "title": item.findtext("title"),
                "creator": item.findtext("dc:creator", namespaces=NAMESPACES),
                "publisher": item.findtext("dc:publisher", namespaces=NAMESPACES),
                "source_url": item.findtext("link"),
                "digitized_pids": digitized_pids(item),
            }
            for item in channel.findall("item")
        ],
    }


@validate_call
async def get_digitized_pages(
    pid: Annotated[str, Field(pattern=r"^[0-9]{1,20}$")],
    limit: Limit = 10,
    start: Annotated[int, Field(ge=1)] = 1,
) -> dict[str, Any]:
    """List public IIIF page links for an NDL Digital Collections PID. Start is one-based."""
    manifest_url = f"https://dl.ndl.go.jp/api/iiif/{pid}/manifest.json"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(manifest_url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (403, 404):
            raise ValueError("No public IIIF manifest is available for this PID.") from None
        raise ValueError(f"NDL IIIF returned HTTP {exc.response.status_code}.") from None
    except httpx.RequestError:
        raise ValueError("Could not reach NDL Digital Collections.") from None

    try:
        manifest = response.json()
        canvases = manifest["sequences"][0]["canvases"]
        if not isinstance(canvases, list):
            raise ValueError
        pages = []
        for index, canvas in enumerate(canvases[start - 1 : start - 1 + limit], start):
            pages.append(
                {
                    "page": index,
                    "label": canvas.get("label"),
                    "canvas_url": canvas["@id"],
                    "image_urls": [image["resource"]["@id"] for image in canvas.get("images", [])],
                }
            )
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise ValueError("NDL returned an unexpected IIIF manifest.") from None
    next_start = start + len(pages)
    return {
        "pid": pid,
        "title": manifest.get("label"),
        "page_count": len(canvases),
        "pages": pages,
        "next_start": next_start if pages and next_start <= len(canvases) else None,
        "source_url": f"https://dl.ndl.go.jp/pid/{pid}",
        "manifest_url": manifest_url,
        "license_url": manifest.get("license"),
        "attribution": manifest.get("attribution"),
    }
