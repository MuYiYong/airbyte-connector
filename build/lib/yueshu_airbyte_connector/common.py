from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ConnectionConfig:
    host: str
    port: int
    username: str
    password: str
    graph: Optional[str] = None
    check_query: Optional[str] = None
    setup_queries: Optional[List[str]] = None


@dataclass
class ReadQuery:
    name: str
    query: str


@dataclass
class WriteQuery:
    stream: str
    query_template: str
    write_mode: Optional[str] = None


@dataclass
class SourceConfig(ConnectionConfig):
    read_queries: List[ReadQuery] = None


@dataclass
class DestinationConfig(ConnectionConfig):
    write_queries: List[WriteQuery] = None


DEFAULT_CHECK_QUERY = "SHOW CURRENT_USER"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_config_from_env_or_path(config_path: Optional[str]) -> Dict[str, Any]:
    if config_path:
        return load_json(config_path)
    raw = os.environ.get("AIRBYTE_CONFIG")
    if raw:
        return json.loads(raw)
    raise ValueError("Missing config: provide --config or AIRBYTE_CONFIG")


def json_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def emit_message(message: Dict[str, Any]) -> None:
    sys.stdout.write(json_dumps(message) + "\n")
    sys.stdout.flush()


def log(message: str) -> None:
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def to_source_config(data: Dict[str, Any]) -> SourceConfig:
    read_queries = [ReadQuery(**item) for item in data.get("read_queries", [])]
    return SourceConfig(
        host=data["host"],
        port=int(data["port"]),
        username=data["username"],
        password=data["password"],
        graph=data.get("graph"),
        check_query=data.get("check_query"),
        setup_queries=data.get("setup_queries", []),
        read_queries=read_queries,
    )


def to_destination_config(data: Dict[str, Any]) -> DestinationConfig:
    write_queries = [WriteQuery(**item) for item in data.get("write_queries", [])]
    return DestinationConfig(
        host=data["host"],
        port=int(data["port"]),
        username=data["username"],
        password=data["password"],
        graph=data.get("graph"),
        check_query=data.get("check_query"),
        setup_queries=data.get("setup_queries", []),
        write_queries=write_queries,
    )


def iter_airbyte_messages(stdin: Iterable[str]) -> Iterable[Dict[str, Any]]:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)
