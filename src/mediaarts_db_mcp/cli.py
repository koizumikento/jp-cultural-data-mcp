import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import get_manga_issue_contents, search_manga_issues, search_works


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="mediaarts-db-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser("get-manga-issue-contents", argument_default=SUPPRESS)
    command.add_argument("--issue-id", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.set_defaults(handler=get_manga_issue_contents)

    command = commands.add_parser("search-manga-issues", argument_default=SUPPRESS)
    command.add_argument("--query", required=True)
    command.add_argument("--volume-number")
    command.add_argument("--issue-number")
    command.add_argument("--year", type=int)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.set_defaults(handler=search_manga_issues)

    command = commands.add_parser("search-works", argument_default=SUPPRESS)
    command.add_argument("--query", required=True)
    command.add_argument("--medium", choices=("manga", "anime", "game"), required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.set_defaults(handler=search_works)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
