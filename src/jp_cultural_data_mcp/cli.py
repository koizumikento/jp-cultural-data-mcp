from argparse import ArgumentParser
from collections.abc import Sequence

from japan_search_mcp.cli import run_cli as japan_search_cli
from mediaarts_db_mcp.cli import run_cli as mediaarts_cli
from ndl_search_mcp.cli import run_cli as ndl_cli


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="jp-cultural-data-mcp")
    commands = parser.add_subparsers(required=True)
    commands.add_parser("ndl", help="国立国会図書館", add_help=False).set_defaults(handler=ndl_cli)
    commands.add_parser("japan-search", help="ジャパンサーチ", add_help=False).set_defaults(
        handler=japan_search_cli
    )
    commands.add_parser("mediaarts", help="メディア芸術データベース", add_help=False).set_defaults(
        handler=mediaarts_cli
    )
    arguments, remaining = parser.parse_known_args(argv)
    arguments.handler(remaining)
