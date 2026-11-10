import subprocess
import sys

import pytest
from mcp import Client, StdioServerParameters

from japan_search_mcp import cli as japan_search_cli
from japan_search_mcp.server import create_server as japan_search_server
from jp_cultural_data_mcp import create_server
from jp_cultural_data_mcp.cli import run_cli
from mediaarts_db_mcp import cli as mediaarts_cli
from mediaarts_db_mcp.server import create_server as mediaarts_server
from ndl_search_mcp import cli as ndl_cli
from ndl_search_mcp.server import create_server as ndl_server


@pytest.mark.asyncio
async def test_combined_tools_preserve_source_schemas() -> None:
    expected = []
    for factory in (
        ndl_server,
        japan_search_server,
        mediaarts_server,
    ):
        expected.extend(await factory().list_tools())
    actual = await create_server().list_tools()
    assert len(actual) == 8
    assert len({tool.name for tool in actual}) == len(actual)
    assert {tool.name: tool.model_dump(exclude_none=True) for tool in actual} == {
        tool.name: tool.model_dump(exclude_none=True) for tool in expected
    }


@pytest.mark.asyncio
async def test_combined_stdio_lists_all_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "jp_cultural_data_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert len(result.tools) == 8
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.parametrize(
    "group, module",
    [("ndl", ndl_cli), ("japan-search", japan_search_cli), ("mediaarts", mediaarts_cli)],
)
def test_cli_dispatches_without_changing_arguments(monkeypatch, group, module) -> None:
    calls = []
    monkeypatch.setattr(module, "run_cli", lambda args: calls.append(list(args)))
    from jp_cultural_data_mcp import cli

    monkeypatch.setattr(cli, group.replace("-", "_") + "_cli", module.run_cli)
    run_cli([group, "query", "--limit", "2"])
    assert calls == [["query", "--limit", "2"]]


def test_command_help() -> None:
    for group in ["ndl", "japan-search", "mediaarts"]:
        result = subprocess.run(
            [sys.executable, "-m", "jp_cultural_data_mcp", group, "--help"],
            capture_output=True,
            check=True,
        )
        assert b"usage:" in result.stdout
