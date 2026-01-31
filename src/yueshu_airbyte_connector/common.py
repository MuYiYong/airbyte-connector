from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ConnectionConfig:
    hosts: List[str]
    username: str
    password: str


@dataclass
class SourceConfig(ConnectionConfig):
    pass


@dataclass
class DestinationConfig(ConnectionConfig):
    pass


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


def read_catalog_from_env() -> Optional[Dict[str, Any]]:
    raw = os.environ.get("AIRBYTE_CATALOG")
    if not raw:
        return None
    return json.loads(raw)


def json_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def emit_message(message: Dict[str, Any]) -> None:
    sys.stdout.write(json_dumps(message) + "\n")
    sys.stdout.flush()


def log(message: str) -> None:
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def to_source_config(data: Dict[str, Any]) -> SourceConfig:
    hosts = _normalize_hosts(data)
    return SourceConfig(
        hosts=hosts,
        username=data["username"],
        password=data["password"],
    )


def to_destination_config(data: Dict[str, Any]) -> DestinationConfig:
    hosts = _normalize_hosts(data)
    return DestinationConfig(
        hosts=hosts,
        username=data["username"],
        password=data["password"],
    )


def _normalize_hosts(data: Dict[str, Any]) -> List[str]:
    hosts = data.get("hosts")
    if isinstance(hosts, list) and hosts:
        normalized = [str(item) for item in hosts if item]
        _validate_hosts(normalized)
        return normalized

    host = data.get("host")
    if isinstance(host, list):
        normalized = [str(item) for item in host if item]
        _validate_hosts(normalized)
        return normalized
    if isinstance(host, str) and host:
        _validate_hosts([host])
        return [host]

    raise ValueError("必须提供 host 或 hosts")


def _validate_hosts(hosts: List[str]) -> None:
    for item in hosts:
        if ":" not in item:
            raise ValueError("仅支持 host:port 形式")


def iter_airbyte_messages(stdin: Iterable[str]) -> Iterable[Dict[str, Any]]:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)
