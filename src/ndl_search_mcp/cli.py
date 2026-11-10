import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import get_digitized_pages, search_bibliography


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="ndl-search-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser(
        "search-bibliography",
        help="Search bibliographic records by title, author, or ISBN.",
        argument_default=SUPPRESS,
    )
    command.add_argument("--title")
    command.add_argument("--creator")
    command.add_argument("--isbn")
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.set_defaults(handler=search_bibliography)

    command = commands.add_parser(
        "get-digitized-pages",
        help="List public page links by NDL Digital Collections PID.",
        argument_default=SUPPRESS,
    )
    command.add_argument("--pid", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.set_defaults(handler=get_digitized_pages)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
        payload = result
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
