import httpx
import pytest
import respx

from mediaarts_db_mcp import get_manga_issue_contents, search_manga_issues, search_works
from mediaarts_db_mcp.client import API_URL, ITEM_URL


@pytest.mark.asyncio
@respx.mock
async def test_issue_contents_page() -> None:
    route = respx.get(API_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": {
                    "bindings": [
                        {"title": {"value": "第1話"}, "page": {"value": "11.0"}},
                        {"title": {"value": "第2話"}, "page": {"value": "23.0"}},
                    ]
                }
            },
        )
    )
    result = await get_manga_issue_contents("M123", limit=1, start=3)
    query = route.calls[0].request.url.params["query"]
    assert "id/M123>" in query
    assert "LIMIT 2" in query and "OFFSET 2" in query
    assert result["items"] == [
        {"title": "第1話", "work_title": None, "start_page": "11.0", "category": None}
    ]
    assert result["next_start"] == 4

    with pytest.raises(ValueError, match="issue_id"):
        await get_manga_issue_contents(issue_id="M123> }")
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_search_manga_issues_returns_toc_id() -> None:
    source_url = ITEM_URL + "M535428"
    route = respx.get(API_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": {
                    "bindings": [
                        {
                            "record": {"value": source_url},
                            "title": {"value": "週刊少年マガジン"},
                            "volume": {"value": "53"},
                            "issue": {"value": "24"},
                            "published": {"value": "2011-05-25"},
                        }
                    ]
                }
            },
        )
    )
    result = await search_manga_issues(
        "週刊少年マガジン", volume_number="53", issue_number="24", year=2011, limit=1, start=2
    )
    query = route.calls[0].request.url.params["query"]
    assert "COALESCE(?displayed, ?catalogNumber)" in query
    assert 'STR(?volumeValue) = "53"' in query and 'STR(?numberValue) = "24"' in query
    assert 'STR(?yearValue) = "2011"' in query and "LIMIT 2" in query and "OFFSET 1" in query
    assert result == {
        "items": [
            {
                "issue_id": "M535428",
                "title": "週刊少年マガジン",
                "volume_number": "53",
                "issue_number": "24",
                "published_date": "2011-05-25",
                "source_url": source_url,
            }
        ],
        "next_start": None,
    }


@pytest.mark.asyncio
@respx.mock
async def test_search_works_escapes_title_and_paginates() -> None:
    source_url = ITEM_URL + "C33828"
    route = respx.get(API_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": {
                    "bindings": [
                        {
                            "record": {"value": url},
                            "type": {
                                "value": "https://mediaarts-db.artmuseums.go.jp/data/class#GameWork"
                            },
                            "title": {"value": "スーパーマリオブラザーズ"},
                        }
                        for url in [source_url, ITEM_URL + "C33826"]
                    ]
                }
            },
        )
    )
    result = await search_works('A"B', medium="game", limit=1, start=3)
    query = route.calls[0].request.url.params["query"]
    assert "VALUES ?type { class:GameWork }" in query
    assert r'LCASE("A\"B")' in query
    assert "LIMIT 2" in query and "OFFSET 2" in query
    assert result == {
        "medium": "game",
        "items": [
            {
                "work_id": "C33828",
                "title": "スーパーマリオブラザーズ",
                "category": "GameWork",
                "source_url": source_url,
            }
        ],
        "next_start": 4,
    }
