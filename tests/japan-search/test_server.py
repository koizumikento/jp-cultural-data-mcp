import json
import sys

import httpx
import pytest
import respx
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from japan_search_mcp import create_server
from japan_search_mcp.client import BASE_URL


@pytest.mark.asyncio
async def test_stdio_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "japan_search_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {
        "search_items",
        "get_item",
        "search_collections",
    }
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.asyncio
@respx.mock
async def test_tool_response() -> None:
    route = respx.get(BASE_URL + "search/jps-cross?keyword=art&size=1&from=3").mock(
        return_value=httpx.Response(
            200, json=json.loads('{"hit":10,"list":[{"id":"museum-123","common":{}}]}')
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool("search_items", {"query": "art", "limit": 1, "offset": 3})
    assert route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["offset"] == 3
    assert payload["items"][0]["source_url"] == "https://jpsearch.go.jp/item/museum-123"


@pytest.mark.asyncio
@respx.mock
async def test_search_combines_database_rights_and_type() -> None:
    route = respx.get(
        BASE_URL + "search/jps-cross?keyword=art&size=1&from=0&f-db=syozo&f-rights=pdm&f-type=paint"
    ).mock(return_value=httpx.Response(200, json={"hit": 1, "list": [{"id": "syozo-123"}]}))
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "search_items",
            {
                "query": "art",
                "database": "syozo",
                "rights": "pdm",
                "item_type": "paint",
                "limit": 1,
            },
        )
    assert route.called
    assert not result.is_error


@pytest.mark.parametrize(
    ("kind", "api_path", "viewer_path", "upstream_fields", "expected_fields"),
    [
        ("database", "database", "database", {"apiType": "ok"}, {"api_type": "ok"}),
        ("organization", "organization", "organization", {}, {}),
        ("gallery", "curation", "gallery", {"title": {"ja": "日本語"}}, {}),
        ("theme", "csearch", "csearch", {"databaseIds": ["bibnl"]}, {"database_ids": ["bibnl"]}),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_search_collections(
    kind: str,
    api_path: str,
    viewer_path: str,
    upstream_fields: dict[str, object],
    expected_fields: dict[str, object],
) -> None:
    route = respx.get(
        f"https://jpsearch.go.jp/api/{api_path}/search?keyword=art&size=1&from=2"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "hit": 3,
                "list": [
                    {
                        "id": "example-1",
                        "name": {"ja": "日本語"},
                        "edit": {"userId": "fixture-editor"},
                        **upstream_fields,
                    }
                ],
            },
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "search_collections", {"kind": kind, "query": "art", "limit": 1, "offset": 2}
        )
    assert route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    assert json.loads(result.content[0].text) == {
        "kind": kind,
        "total": 3,
        "offset": 2,
        "collections": [
            {
                "id": "example-1",
                "name": {"ja": "日本語"},
                "source_url": f"https://jpsearch.go.jp/{viewer_path}/example-1",
                **expected_fields,
            }
        ],
    }


@pytest.mark.parametrize("database", ["najda", "syozo"])
@pytest.mark.asyncio
@respx.mock
async def test_scoped_search_uses_database_endpoint(database: str) -> None:
    route = respx.get(BASE_URL + f"search/{database}-default?keyword=art&size=1&from=0").mock(
        return_value=httpx.Response(200, json={"hit": 1, "list": [{"id": f"{database}-123"}]})
    )
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "search_items", {"query": "art", "database": database, "limit": 1}
        )
    assert route.called
    assert not result.is_error
