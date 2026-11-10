import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import COLLECTION_ROUTES, get_item, search_collections, search_items


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="japan-search-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser(
        "search-items", help="Search cultural items.", argument_default=SUPPRESS
    )
    command.add_argument("--query", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.add_argument("--database")
    command.add_argument("--rights")
    command.add_argument("--item-type")
    command.set_defaults(handler=search_items)

    command = commands.add_parser(
        "search-collections",
        help="Find databases, organizations, galleries, or themed searches.",
        argument_default=SUPPRESS,
    )
    command.add_argument("--kind", required=True, choices=COLLECTION_ROUTES)
    command.add_argument("--query")
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.set_defaults(handler=search_collections)

    command = commands.add_parser("get-item", help="Get item metadata.", argument_default=SUPPRESS)
    command.add_argument("--item-id", required=True)
    command.set_defaults(handler=get_item)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
        payload = result
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
