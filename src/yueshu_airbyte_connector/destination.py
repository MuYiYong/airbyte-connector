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
from .gql_generator import (
    generate_gql_from_mapping,
    transform_flat_config_to_mapping,
)
from .nebula_client import NebulaClient, NebulaClientError


def spec() -> Dict[str, Any]:
    return {
        "type": "SPEC",
        "spec": {
            "documentationUrl": "",
            "connectionSpecification": {
                "type": "object",
                "required": ["hosts", "username", "password"],
                "properties": {
                    "hosts": {"type": "array", "items": {"type": "string"}},
                    "username": {"type": "string", "default": "root"},
                    "password": {"type": "string", "airbyte_secret": True, "default": "root"},
                },
            },
        },
    }


def check(config_data: Dict[str, Any]) -> None:
    cfg = to_destination_config(config_data)
    client = NebulaClient(
        hosts=cfg.hosts,
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
    """
    Load write configuration from catalog.
    Supports two mapping formats:
    1. Mapping-based (hierarchical) - preferred
    2. Mapping-based (flat) - auto-converted to hierarchical
    """
    catalog = read_catalog_from_env() or {}
    write_map: Dict[str, Dict[str, Any]] = {}

    for stream_entry in catalog.get("streams", []):
        stream_info = stream_entry.get("stream") or stream_entry
        name = stream_info.get("name")
        if not name:
            continue
        
        config = stream_entry.get("config") or {}
        
        # Priority 1: Check for mapping-based configuration (hierarchical format)
        if "mapping" in config:
            write_map[name] = {
                "mapping_config": {
                    "graph": config.get("graph"),
                    "mapping": config["mapping"],
                    "write_mode": config.get("write_mode", "insert or ignore"),
                },
                "graph": config.get("graph"),
                "setup_queries": config.get("setup_queries") or [],
            }
            continue
        
        # Priority 2: Check for flat mapping configuration
        if "mapping_type" in config:
            # Transform flat config to standard mapping format
            mapping_config = transform_flat_config_to_mapping(config)
            write_map[name] = {
                "mapping_config": mapping_config,
                "graph": config.get("graph"),
                "setup_queries": config.get("setup_queries") or [],
            }
            continue

    return write_map


def write(config_data: Dict[str, Any], stdin: Iterable[str]) -> None:
    cfg = to_destination_config(config_data)
    write_map = _load_write_map(config_data)
    if not write_map:
        raise ValueError(
            "配置不能为空，请在 AIRBYTE_CATALOG 的 stream config 中提供 mapping 配置"
        )
    client = NebulaClient(
        hosts=cfg.hosts,
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
            
            # Handle graph switching
            graph = write_item.get("graph")
            if graph and graph != current_graph:
                client.execute(f"SESSION SET GRAPH {graph}")
                current_graph = graph
            
            # Execute setup queries once per stream
            if stream not in initialized_streams:
                for query in write_item.get("setup_queries") or []:
                    if query:
                        client.execute(query)
                initialized_streams.add(stream)
            
            # Use mapping-based GQL generation
            mapping_config = write_item.get("mapping_config", {})
            try:
                gql = generate_gql_from_mapping(mapping_config, data)
                write_mode = mapping_config.get("write_mode")
            except Exception as e:
                log(f"生成 GQL 失败: {e}, stream={stream}, data={data}")
                raise ValueError(f"GQL 生成失败 (stream: {stream}): {e}")
            
            # Apply write mode
            gql = _apply_table_insert(gql, write_mode)
            
            log(f"写入流 {stream}: {gql}")
            client.execute(gql)
        
        emit_message({"type": "STATE", "state": {"last_write": True}})
    finally:
        client.close()
