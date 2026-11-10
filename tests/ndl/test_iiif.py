import httpx
import pytest
import respx

from ndl_search_mcp import get_digitized_pages


@pytest.mark.asyncio
@respx.mock
async def test_manifest_pagination_and_missing_manifest() -> None:
    route = respx.get("https://dl.ndl.go.jp/api/iiif/123/manifest.json").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "label": "資料",
                    "license": "https://example.org/rights",
                    "sequences": [
                        {
                            "canvases": [
                                {"@id": "https://example.org/canvas/1"},
                                {
                                    "@id": "https://example.org/canvas/2",
                                    "images": [
                                        {"resource": {"@id": "https://example.org/image/2"}}
                                    ],
                                },
                            ]
                        }
                    ],
                },
            ),
            httpx.Response(404),
        ],
    )
    result = await get_digitized_pages("123", limit=1, start=2)
    assert route.called
    assert result["page_count"] == 2
    assert result["next_start"] is None
    assert result["pages"][0]["page"] == 2
    assert result["pages"][0]["image_urls"] == ["https://example.org/image/2"]
    with pytest.raises(ValueError, match="No public IIIF manifest"):
        await get_digitized_pages("123")
