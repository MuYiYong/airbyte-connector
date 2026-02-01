from __future__ import annotations

from typing import Any, List, Optional

from .common import log


class NebulaClientError(RuntimeError):
    pass


def _import_client() -> Any:
    """导入 nebula5_python 的 NebulaClient"""
    try:
        from nebulagraph_python import NebulaClient as NebulaClientImpl
        return NebulaClientImpl
    except ImportError as exc:
        raise NebulaClientError(
            f"无法导入 nebula5_python: {exc}. 请确保已安装 nebula5_python==5.2.1"
        ) from exc


class NebulaClient:
    """
    封装 nebula5_python 的 NebulaClient
    参考: https://github.com/vesoft-inc/nebula-python/tree/v5.2.1/docs/1_started.md
    """
    
    def __init__(
        self,
        hosts: List[str],
        username: str,
        password: str,
        graph: Optional[str] = None,
    ) -> None:
        self._hosts = hosts
        self._username = username
        self._password = password
        self._graph = graph
        self._client = None

    def connect(self) -> None:
        """
        连接到 Nebula Graph (Yueshu 5.2.0)
        使用 context manager 方式创建客户端
        """
        client_cls = _import_client()
        
        # 创建同步客户端实例
        # 参考: https://github.com/vesoft-inc/nebula-python/tree/v5.2.1/docs/1_started.md
        self._client = client_cls(
            hosts=self._hosts,
            username=self._username,
            password=self._password,
        )
        
        # 注意: Yueshu 5.2.0 不需要执行 OPEN GRAPH 或 USE 命令
        # 直接在 execute() 中执行 INSERT 等 GQL 语句即可
        # graph 参数存储在 self._graph 中作为上下文记录

    def close(self) -> None:
        """关闭连接"""
        if self._client is not None:
            try:
                self._client.close()
            except Exception as exc:  # noqa: BLE001
                log(f"关闭客户端失败: {exc}")

    def execute(self, query: str) -> Any:
        """
        执行 GQL 查询
        返回 ResultSet 对象
        """
        if self._client is None:
            raise NebulaClientError("客户端未初始化，请先调用 connect()")
        
        result = self._client.execute(query)
        
        # 检查执行是否成功
        if hasattr(result, "is_succeeded"):
            # is_succeeded 是一个属性，不是方法
            is_succeeded = result.is_succeeded
            if callable(is_succeeded):
                # 如果是方法，则调用
                if not is_succeeded():
                    error_msg = getattr(result, "error_msg", "执行失败")
                    raise NebulaClientError(f"查询执行失败: {error_msg}")
            else:
                # 如果是属性，直接判断
                if not is_succeeded:
                    error_msg = getattr(result, "error_msg", "执行失败")
                    raise NebulaClientError(f"查询执行失败: {error_msg}")
        
        return result

    @staticmethod
    def result_to_payload(result: Any) -> str:
        """
        将 ResultSet 转换为字符串格式
        支持 as_primitive_by_column() 和 as_primitive_by_row() 方法
        """
        if hasattr(result, "as_primitive_by_column"):
            try:
                return str(result.as_primitive_by_column())
            except Exception:  # noqa: BLE001
                pass
        if hasattr(result, "as_primitive_by_row"):
            try:
                return str(list(result.as_primitive_by_row()))
            except Exception:  # noqa: BLE001
                pass
        return str(result)
