from __future__ import annotations

import re
from typing import Any, Dict, Iterable

from .common import (
    DEFAULT_CHECK_QUERY,
    emit_message,
    iter_airbyte_messages,
    log,
    to_destination_config,
)
from .nebula_client import NebulaClient, NebulaClientError


def spec() -> Dict[str, Any]:
    return {
        "type": "SPEC",
        "spec": {
            "documentationUrl": "",
            "connectionSpecification": {
                "type": "object",
                "required": ["host", "port", "username", "password"],
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                    "username": {"type": "string"},
                    "password": {"type": "string", "airbyte_secret": True},
                    "graph": {"type": "string"},
                    "check_query": {"type": "string"},
                    "setup_queries": {"type": "array", "items": {"type": "string"}},
                    "write_queries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["stream", "query_template"],
                            "properties": {
                                "stream": {"type": "string"},
                                "query_template": {"type": "string"},
                                "write_mode": {
                                    "type": "string",
                                    "enum": [
                                        "insert",
                                        "insert or replace",
                                        "insert or ignore",
                                        "insert or update",
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
    }


def check(config_data: Dict[str, Any]) -> None:
    cfg = to_destination_config(config_data)
    client = NebulaClient(
        host=cfg.host,
        port=cfg.port,
        username=cfg.username,
        password=cfg.password,
        graph=cfg.graph,
    )
    try:
        client.connect()
        query = cfg.check_query or DEFAULT_CHECK_QUERY
        client.execute(query)
        emit_message(
            {
                "type": "CONNECTION_STATUS",
                "connectionStatus": {"status": "SUCCEEDED"},
            }
        )
    except NebulaClientError as exc:
        emit_message(
            {
                "type": "CONNECTION_STATUS",
                "connectionStatus": {"status": "FAILED", "message": str(exc)},
            }
        )
    finally:
        client.close()


def _apply_template(template: str, record: Dict[str, Any]) -> str:
    try:
        return template.format(**record)
    except Exception:
        return template


_WRITE_MODE_MAP = {
    "insert": "INSERT",
    "insert or replace": "INSERT OR REPLACE",
    "insert or ignore": "INSERT OR IGNORE",
    "insert or update": "INSERT OR UPDATE",
}


def _normalize_write_mode(write_mode: str | None) -> str:
    if not write_mode:
        return _WRITE_MODE_MAP["insert or ignore"]
    normalized = write_mode.strip().lower()
    return _WRITE_MODE_MAP.get(normalized, _WRITE_MODE_MAP["insert or ignore"])


def _replace_first_insert(query: str, insert_keyword: str) -> str:
    return re.sub(r"\binsert\b", insert_keyword, query, count=1, flags=re.IGNORECASE)


def _apply_table_insert(query: str, write_mode: str | None) -> str:
    insert_keyword = _normalize_write_mode(write_mode)
    stripped = query.lstrip()
    upper = stripped.upper()

    if upper.startswith("TABLE "):
        if "INSERT" in upper:
            return _replace_first_insert(stripped, insert_keyword)
        return stripped

    if upper.startswith("MATCH "):
        if "INSERT" in upper:
            return f"TABLE {_replace_first_insert(stripped, insert_keyword)}"
        return f"TABLE {stripped}"

    if "INSERT" in upper:
        replaced = _replace_first_insert(stripped, insert_keyword)
        return f"TABLE {replaced}"

    return query


def write(config_data: Dict[str, Any], stdin: Iterable[str]) -> None:
    cfg = to_destination_config(config_data)
    if not cfg.write_queries:
        raise ValueError("write_queries 不能为空")
    write_map = {item.stream: item for item in cfg.write_queries}
    client = NebulaClient(
        host=cfg.host,
        port=cfg.port,
        username=cfg.username,
        password=cfg.password,
        graph=cfg.graph,
    )
    try:
        client.connect()
        for query in cfg.setup_queries or []:
            if query:
                client.execute(query)
        for message in iter_airbyte_messages(stdin):
            if message.get("type") != "RECORD":
                continue
            record = message.get("record", {})
            stream = record.get("stream")
            data = record.get("data", {})
            write_item = write_map.get(stream)
            if not write_item:
                continue
            gql = _apply_template(write_item.query_template, data)
            gql = _apply_table_insert(gql, write_item.write_mode)
            log(f"写入流 {stream}")
            client.execute(gql)
        emit_message({"type": "STATE", "state": {"last_write": True}})
    finally:
        client.close()
