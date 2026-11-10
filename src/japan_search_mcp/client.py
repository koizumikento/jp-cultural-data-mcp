from __future__ import annotations

from typing import Annotated, Any, Literal

import httpx
from pydantic import Field, validate_call

SITE_URL = "https://jpsearch.go.jp"
BASE_URL = f"{SITE_URL}/api/item/"
Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0, le=10000)]
ItemId = Annotated[str, Field(pattern=r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,199}$")]
Facet = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")]
CollectionKind = Literal["database", "organization", "gallery", "theme"]
COLLECTION_ROUTES = {
    "database": ("database", "database"),
    "organization": ("organization", "organization"),
    "gallery": ("curation", "gallery"),
    "theme": ("csearch", "csearch"),
}


def item_summary(item: dict[str, Any]) -> dict[str, Any]:
    item_id = item["id"]
    return {
        "id": item_id,
        "metadata": item.get("common"),
        "source_url": f"https://jpsearch.go.jp/item/{item_id}",
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


async def get_json(path: str, **params: str | int | None) -> dict[str, Any]:
    response = await get_response(path, **params)
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Upstream response was not a JSON object.")
    return data


@validate_call
async def search_items(
    query: Query,
    limit: Limit = 10,
    offset: Offset = 0,
    database: ItemId | None = None,
    rights: Facet | None = None,
    item_type: Facet | None = None,
) -> dict[str, Any]:
    """Search items by keyword, database ID, rights code (e.g. cc0), and type (e.g. paint)."""
    params = {"keyword": query, "size": limit, "from": offset}
    if database in {"najda", "syozo"} and rights is None and item_type is None:
        data = await get_json(f"search/{database}-default", **params)
    else:
        data = await get_json(
            "search/jps-cross",
            **params,
            **{"f-db": database, "f-rights": rights, "f-type": item_type},
        )
    return {
        "total": data["hit"],
        "offset": offset,
        "items": [item_summary(item) for item in data.get("list", [])],
    }


@validate_call
async def search_collections(
    kind: CollectionKind,
    query: Query | None = None,
    limit: Limit = 10,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Find databases, organizations, galleries, or themed searches and their public pages."""
    api_path, viewer_path = COLLECTION_ROUTES[kind]
    data = await get_json(
        f"{SITE_URL}/api/{api_path}/search", **{"keyword": query, "size": limit, "from": offset}
    )
    collections = []
    for record in data.get("list", []):
        record_id = record["id"]
        entry = {
            "id": record_id,
            "name": record.get("title" if kind == "gallery" else "name"),
            "source_url": f"{SITE_URL}/{viewer_path}/{record_id}",
        }
        if kind == "database":
            entry["api_type"] = record.get("apiType")
        if kind == "theme":
            entry["database_ids"] = record.get("databaseIds", [])
        collections.append(entry)
    return {"kind": kind, "total": data["hit"], "offset": offset, "collections": collections}


@validate_call
async def get_item(item_id: ItemId) -> dict[str, Any]:
    """Get published metadata for an item ID, including its Japan Search page."""
    item = await get_json(item_id)
    return {**item_summary(item), "metadata": item}
