from mcp.server import MCPServer

from japan_search_mcp import server as japan_search_server
from mediaarts_db_mcp import server as mediaarts_server
from ndl_search_mcp import server as ndl_server


def create_server() -> MCPServer:
    mcp = MCPServer("jp-cultural-data-mcp")
    mcp.tool(annotations=ndl_server.READ_ONLY)(ndl_server.search_bibliography)
    mcp.tool(annotations=ndl_server.READ_ONLY)(ndl_server.get_digitized_pages)
    mcp.tool(annotations=japan_search_server.READ_ONLY)(japan_search_server.search_items)
    mcp.tool(annotations=japan_search_server.READ_ONLY)(japan_search_server.get_item)
    mcp.tool(annotations=japan_search_server.READ_ONLY)(japan_search_server.search_collections)
    mcp.tool(annotations=mediaarts_server.READ_ONLY)(
        mediaarts_server._tool_errors(mediaarts_server.get_manga_issue_contents)
    )
    mcp.tool(annotations=mediaarts_server.READ_ONLY)(
        mediaarts_server._tool_errors(mediaarts_server.search_manga_issues)
    )
    mcp.tool(annotations=mediaarts_server.READ_ONLY)(
        mediaarts_server._tool_errors(mediaarts_server.search_works)
    )
    return mcp
