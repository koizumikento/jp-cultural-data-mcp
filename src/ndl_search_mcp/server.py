from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .client import get_digitized_pages, search_bibliography

READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, destructive_hint=False, open_world_hint=True
)


def create_server() -> MCPServer:
    mcp = MCPServer("ndl-search-mcp")
    mcp.tool(annotations=READ_ONLY)(search_bibliography)
    mcp.tool(annotations=READ_ONLY)(get_digitized_pages)
    return mcp
