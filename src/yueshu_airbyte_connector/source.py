from __future__ import annotations

import time
from typing import Any, Dict, List

from .common import (
    DEFAULT_CHECK_QUERY,
    emit_message,
    log,
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
                "required": ["host", "port", "username", "password"],
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                    "username": {"type": "string"},
                    "password": {"type": "string", "airbyte_secret": True},
                    "graph": {"type": "string"},
                    "check_query": {"type": "string"},
                    "setup_queries": {"type": "array", "items": {"type": "string"}},
                    "read_queries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "query"],
                            "properties": {
                                "name": {"type": "string"},
                                "query": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }


def check(config_data: Dict[str, Any]) -> None:
    cfg = to_source_config(config_data)
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


def discover(config_data: Dict[str, Any]) -> None:
    cfg = to_source_config(config_data)
    streams: List[Dict[str, Any]] = []
    for query in cfg.read_queries or []:
        streams.append(
            {
                "name": query.name,
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


def read(config_data: Dict[str, Any]) -> None:
    cfg = to_source_config(config_data)
    if not cfg.read_queries:
        raise ValueError("read_queries 不能为空")
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
        for idx, query in enumerate(cfg.read_queries):
            log(f"执行读查询: {query.name}")
            result = client.execute(query.query)
            payload = client.result_to_payload(result)
            emit_message(
                {
                    "type": "RECORD",
                    "record": {
                        "stream": query.name,
                        "data": {
                            "payload": payload,
                            "query": query.query,
                            "index": idx,
                        },
                        "emitted_at": int(time.time() * 1000),
                    },
                }
            )
        emit_message({"type": "STATE", "state": {"last_read": int(time.time())}})
    finally:
        client.close()
