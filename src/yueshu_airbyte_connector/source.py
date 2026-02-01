from __future__ import annotations

import time
from typing import Any, Dict, List

from .common import (
    DEFAULT_CHECK_QUERY,
    emit_message,
    log,
    read_catalog_from_env,
    to_source_config,
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
    cfg = to_source_config(config_data)
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


def discover(config_data: Dict[str, Any]) -> None:
    streams: List[Dict[str, Any]] = []
    catalog = read_catalog_from_env() or {}
    for stream_entry in catalog.get("streams", []):
        stream_info = stream_entry.get("stream") or stream_entry
        name = stream_info.get("name")
        if not name:
            continue
        streams.append(
            {
                "name": name,
                "supported_sync_modes": ["full_refresh"],
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "payload": {"type": "string"},
                        "query": {"type": "string"},
                        "index": {"type": "integer"},
                    },
                },
            }
        )
    emit_message({"type": "CATALOG", "catalog": {"streams": streams}})


def _load_read_queries(config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    catalog = read_catalog_from_env() or {}
    queries: List[Dict[str, Any]] = []
    for stream_entry in catalog.get("streams", []):
        stream_info = stream_entry.get("stream") or stream_entry
        name = stream_info.get("name")
        if not name:
            continue
        config = stream_entry.get("config") or {}
        query = config.get("read_query") or config.get("query")
        if not query:
            continue
        queries.append(
            {
                "name": name,
                "query": query,
                "graph": config.get("graph"),
                "setup_queries": config.get("setup_queries") or [],
            }
        )

    if queries:
        return queries

    legacy = config_data.get("read_queries", [])
    for item in legacy:
        if not item:
            continue
        queries.append(
            {
                "name": item.get("name"),
                "query": item.get("query"),
                "graph": item.get("graph"),
                "setup_queries": item.get("setup_queries") or [],
            }
        )
    return queries


def read(config_data: Dict[str, Any]) -> None:
    cfg = to_source_config(config_data)
    read_queries = _load_read_queries(config_data)
    if not read_queries:
        raise ValueError("read_queries 不能为空，请在 AIRBYTE_CATALOG 的 stream config 中提供 read_query")
    client = NebulaClient(
        hosts=cfg.hosts,
        username=cfg.username,
        password=cfg.password,
    )
    try:
        client.connect()
        current_graph = None
        for idx, query in enumerate(read_queries):
            name = query.get("name")
            gql = query.get("query")
            if not name or not gql:
                continue
            graph = query.get("graph")
            # 注意: Yueshu 不需要执行 OPEN GRAPH 或 USE 命令
            # 直接执行 GQL 语句即可，graph 参数仅作为上下文记录
            if graph and graph != current_graph:
                current_graph = graph
            for setup in query.get("setup_queries") or []:
                if setup:
                    client.execute(setup)
            log(f"执行读查询: {name}")
            result = client.execute(gql)
            payload = client.result_to_payload(result)
            emit_message(
                {
                    "type": "RECORD",
                    "record": {
                        "stream": name,
                        "data": {
                            "payload": payload,
                            "query": gql,
                            "index": idx,
                        },
                        "emitted_at": int(time.time() * 1000),
                    },
                }
            )
        emit_message({"type": "STATE", "state": {"last_read": int(time.time())}})
    finally:
        client.close()
