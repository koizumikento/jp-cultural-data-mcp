from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .client import get_item, search_collections, search_items

READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, destructive_hint=False, open_world_hint=True
)


def create_server() -> MCPServer:
    mcp = MCPServer("japan-search-mcp")
    mcp.tool(annotations=READ_ONLY)(search_items)
    mcp.tool(annotations=READ_ONLY)(get_item)
    mcp.tool(annotations=READ_ONLY)(search_collections)
    return mcp
