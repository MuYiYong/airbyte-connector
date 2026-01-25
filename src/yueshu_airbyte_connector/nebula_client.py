from __future__ import annotations

import importlib
from typing import Any, List, Optional, Tuple

from .common import log


class NebulaClientError(RuntimeError):
    pass


def _import_pool() -> Tuple[str, Any, Any]:
    module_name = "nebulagraph_python.client.pool"
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        raise NebulaClientError(
            f"无法导入 nebula5-python 模块 {module_name}: {exc}"
        ) from exc

    pool_cls = getattr(module, "NebulaPool", None)
    config_cls = getattr(module, "NebulaPoolConfig", None)
    if pool_cls is None or config_cls is None:
        raise NebulaClientError("nebula5-python 未提供 NebulaPool/NebulaPoolConfig")

    return module_name, pool_cls, config_cls


class NebulaClient:
    def __init__(
        self,
        hosts: List[str],
        port: Optional[int],
        username: str,
        password: str,
        graph: Optional[str] = None,
    ) -> None:
        self._hosts = hosts
        self._port = port
        self._username = username
        self._password = password
        self._graph = graph
        self._pool = None

    def connect(self) -> None:
        module_name, pool_cls, config_cls = _import_pool()
        config = config_cls()
        if hasattr(config, "max_client_size"):
            config.max_client_size = 5
        if hasattr(config, "max_connection_pool_size"):
            config.max_connection_pool_size = 5
        elif hasattr(config, "max_conn_pool_size"):
            config.max_conn_pool_size = 5

        host_list = []
        for host in self._hosts:
            if ":" in host:
                host_list.append(host)
                continue
            if self._port is None:
                raise NebulaClientError("未提供 port，且 host 未包含端口")
            host_list.append(f"{host}:{self._port}")
        self._pool = pool_cls(
            hosts=host_list,
            username=self._username,
            password=self._password,
            pool_config=config,
        )

        if self._graph:
            self.execute(f"SESSION SET GRAPH {self._graph}")

    def close(self) -> None:
        if self._pool is not None:
            try:
                self._pool.close()
            except Exception as exc:  # noqa: BLE001
                log(f"关闭连接池失败: {exc}")

    def execute(self, query: str) -> Any:
        if self._pool is None:
            raise NebulaClientError("连接池未初始化")
        result = self._pool.execute(query)
        if hasattr(result, "raise_on_error"):
            result.raise_on_error()
        elif hasattr(result, "is_succeeded"):
            if not result.is_succeeded():
                error_msg = getattr(result, "error_msg", None)
                raise NebulaClientError(error_msg or "执行失败")
        return result

    @staticmethod
    def result_to_payload(result: Any) -> str:
        if hasattr(result, "as_primitive_by_row"):
            try:
                return str(result.as_primitive_by_row())
            except Exception:  # noqa: BLE001
                pass
        if hasattr(result, "to_string"):
            try:
                return result.to_string()
            except Exception:  # noqa: BLE001
                pass
        return str(result)
