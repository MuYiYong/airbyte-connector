from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict

from . import destination, source
from .common import emit_message, read_config_from_env_or_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("yueshu-airbyte")
    parser.add_argument("--connector-type", choices=["source", "destination"], default=None)
    parser.add_argument("command", nargs="?", choices=["spec", "check", "discover", "read", "write"], default=None)
    parser.add_argument("--command", dest="command_opt", choices=["spec", "check", "discover", "read", "write"], required=False)
    parser.add_argument("--config", required=False)
    return parser.parse_args()


def _get_connector(args: argparse.Namespace):
    connector_type = args.connector_type or os.environ.get("CONNECTOR_TYPE", "source")
    return source if connector_type == "source" else destination


def _get_command(args: argparse.Namespace) -> str:
    return args.command or args.command_opt or os.environ.get("AIRBYTE_COMMAND", "spec")


def _read_config(args: argparse.Namespace) -> Dict[str, Any]:
    return read_config_from_env_or_path(args.config)


def main() -> None:
    args = _parse_args()
    connector = _get_connector(args)
    command = _get_command(args)

    if command == "spec":
        emit_message(connector.spec())
        return

    if command in {"check", "discover", "read", "write"}:
        config = _read_config(args)

    if command == "check":
        connector.check(config)
        return

    if command == "discover":
        connector.discover(config)
        return

    if command == "read":
        connector.read(config)
        return

    if command == "write":
        connector.write(config, sys.stdin)
        return

    raise SystemExit(f"未知命令: {command}")


if __name__ == "__main__":
    main()
