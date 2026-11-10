import json
import sys

import httpx
import pytest
import respx
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from ndl_search_mcp import create_server
from ndl_search_mcp.client import BASE_URL


@pytest.mark.asyncio
async def test_stdio_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "ndl_search_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {"search_bibliography", "get_digitized_pages"}
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.asyncio
@respx.mock
async def test_tool_response() -> None:
    route = respx.get(BASE_URL + "opensearch?title=Genji&cnt=1&idx=1").mock(
        return_value=httpx.Response(
            200,
            text="""<rss xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:opensearch="http://a9.com/-/spec/opensearchrss/1.0/">
  <channel>
    <opensearch:totalResults>1</opensearch:totalResults>
    <item>
      <title>Genji</title><dc:creator>Author</dc:creator>
      <link>https://ndlsearch.ndl.go.jp/books/example</link>
    </item>
  </channel>
</rss>""",
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool("search_bibliography", {"title": "Genji", "limit": 1})
    assert route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["total"] == 1
    assert payload["records"][0]["creator"] == "Author"
    assert payload["records"][0]["digitized_pids"] == []


@pytest.mark.parametrize(
    ("isbn", "normalized_isbn"),
    [("978-4-00-310101-8", "9784003101018"), ("4-00-310101-4", "4003101014")],
)
@pytest.mark.asyncio
@respx.mock
async def test_isbn_search_returns_explicit_digitized_pids(isbn: str, normalized_isbn: str) -> None:
    route = respx.get(BASE_URL + f"opensearch?cnt=1&idx=1&isbn={normalized_isbn}").mock(
        return_value=httpx.Response(
            200,
            text="""<rss xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
  <channel><item>
    <title>Book</title>
    <link>https://ndlsearch.ndl.go.jp/books/R100000039-I99</link>
    <dc:identifier>info:ndljp/pid/1234</dc:identifier>
    <dc:identifier>info:ndljp/pid/1234-extra</dc:identifier>
    <rdfs:seeAlso rdf:resource="https://dl.ndl.go.jp/pid/1234"/>
    <rdfs:seeAlso rdf:resource="https://dl.ndl.go.jp/pid/5678"/>
    <rdfs:seeAlso rdf:resource="https://dl.ndl.go.jp.example.com/pid/9876"/>
  </item></channel>
</rss>""",
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool("search_bibliography", {"isbn": isbn, "limit": 1})
    assert route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["records"][0]["digitized_pids"] == ["1234", "5678"]
