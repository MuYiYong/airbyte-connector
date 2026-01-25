from __future__ import annotations

import re
from typing import Any, Dict, Iterable

from .common import (
    DEFAULT_CHECK_QUERY,
    emit_message,
    iter_airbyte_messages,
    log,
    read_catalog_from_env,
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
                "required": ["username", "password"],
                "properties": {
                    "host": {"type": "string"},
                    "hosts": {"type": "array", "items": {"type": "string"}},
                    "port": {"type": "integer"},
                    "username": {"type": "string"},
                    "password": {"type": "string", "airbyte_secret": True},
                },
            },
        },
    }


def check(config_data: Dict[str, Any]) -> None:
    cfg = to_destination_config(config_data)
    client = NebulaClient(
        hosts=cfg.hosts,
        port=cfg.port,
        username=cfg.username,
        password=cfg.password,
    )
    try:
        client.connect()
        client.execute(DEFAULT_CHECK_QUERY)
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


def _load_write_map(config_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    catalog = read_catalog_from_env() or {}
    write_map: Dict[str, Dict[str, Any]] = {}

    for stream_entry in catalog.get("streams", []):
        stream_info = stream_entry.get("stream") or stream_entry
        name = stream_info.get("name")
        if not name:
            continue
        config = stream_entry.get("config") or {}
        template = config.get("write_query_template") or config.get("query_template")
        if not template:
            continue
        write_map[name] = {
            "query_template": template,
            "write_mode": config.get("write_mode"),
            "graph": config.get("graph"),
            "setup_queries": config.get("setup_queries") or [],
        }

    if write_map:
        return write_map

    legacy = config_data.get("write_queries", [])
    for item in legacy:
        if not item:
            continue
        name = item.get("stream")
        template = item.get("query_template")
        if not name or not template:
            continue
        write_map[name] = {
            "query_template": template,
            "write_mode": item.get("write_mode"),
            "graph": item.get("graph"),
            "setup_queries": item.get("setup_queries") or [],
        }
    return write_map


def write(config_data: Dict[str, Any], stdin: Iterable[str]) -> None:
    cfg = to_destination_config(config_data)
    write_map = _load_write_map(config_data)
    if not write_map:
        raise ValueError("write_queries 不能为空，请在 AIRBYTE_CATALOG 的 stream config 中提供 write_query_template")
    client = NebulaClient(
        hosts=cfg.hosts,
        port=cfg.port,
        username=cfg.username,
        password=cfg.password,
    )
    try:
        client.connect()
        current_graph = None
        initialized_streams = set()
        for message in iter_airbyte_messages(stdin):
            if message.get("type") != "RECORD":
                continue
            record = message.get("record", {})
            stream = record.get("stream")
            data = record.get("data", {})
            write_item = write_map.get(stream)
            if not write_item:
                continue
            graph = write_item.get("graph")
            if graph and graph != current_graph:
                client.execute(f"SESSION SET GRAPH {graph}")
                current_graph = graph
            if stream not in initialized_streams:
                for query in write_item.get("setup_queries") or []:
                    if query:
                        client.execute(query)
                initialized_streams.add(stream)
            gql = _apply_template(write_item.get("query_template", ""), data)
            gql = _apply_table_insert(gql, write_item.get("write_mode"))
            log(f"写入流 {stream}")
            client.execute(gql)
        emit_message({"type": "STATE", "state": {"last_write": True}})
    finally:
        client.close()
