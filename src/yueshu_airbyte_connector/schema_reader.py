"""
Schema Reader - 从 NebulaGraph 读取 graph schema

支持读取点类型（TAG）和边类型（EDGE）的完整定义，包括：
- 字段名称
- 数据类型
- 主键信息
- 边的起点、终点类型
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .common import log


@dataclass
class PropertySchema:
    """属性定义"""
    name: str
    type: str  # NebulaGraph 数据类型，如 string, int64, double, date, datetime 等
    nullable: bool = True
    default_value: Optional[Any] = None


@dataclass
class VertexSchema:
    """点类型定义"""
    label: str  # TAG 名称
    properties: List[PropertySchema] = field(default_factory=list)
    
    def get_property(self, name: str) -> Optional[PropertySchema]:
        """根据属性名获取属性定义"""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None


@dataclass
class EdgeSchema:
    """边类型定义"""
    label: str  # EDGE 名称
    properties: List[PropertySchema] = field(default_factory=list)
    
    def get_property(self, name: str) -> Optional[PropertySchema]:
        """根据属性名获取属性定义"""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None


@dataclass
class GraphSchema:
    """图 schema 定义"""
    graph_name: str
    vertices: Dict[str, VertexSchema] = field(default_factory=dict)
    edges: Dict[str, EdgeSchema] = field(default_factory=dict)
    
    def get_vertex_schema(self, label: str) -> Optional[VertexSchema]:
        """根据 TAG 名获取点类型定义"""
        return self.vertices.get(label)
    
    def get_edge_schema(self, label: str) -> Optional[EdgeSchema]:
        """根据 EDGE 名获取边类型定义"""
        return self.edges.get(label)


def read_graph_schema(client: Any, graph_name: str) -> GraphSchema:
    """
    读取图的完整 schema
    
    Args:
        client: NebulaClient 实例
        graph_name: 图空间名称
        
    Returns:
        GraphSchema 实例
    """
    schema = GraphSchema(graph_name=graph_name)
    
    # 注意: Yueshu 5.2.0 不支持 USE 命令，直接执行 SHOW TAGS/SHOW EDGES 即可
    log(f"正在读取图 {graph_name} 的 schema...")
    
    # 读取所有 TAG
    try:
        result = client.execute("SHOW TAGS")
        tags = _parse_show_tags(result)
        log(f"发现 {len(tags)} 个点类型: {tags}")
        
        for tag_name in tags:
            tag_schema = _read_tag_schema(client, tag_name)
            if tag_schema:
                schema.vertices[tag_name] = tag_schema
    except Exception as e:
        log(f"读取 TAG 失败: {e}")
    
    # 读取所有 EDGE
    try:
        result = client.execute("SHOW EDGES")
        edges = _parse_show_edges(result)
        log(f"发现 {len(edges)} 个边类型: {edges}")
        
        for edge_name in edges:
            edge_schema = _read_edge_schema(client, edge_name)
            if edge_schema:
                schema.edges[edge_name] = edge_schema
    except Exception as e:
        log(f"读取 EDGE 失败: {e}")
    
    return schema


def _parse_show_tags(result: Any) -> List[str]:
    """解析 SHOW TAGS 的结果"""
    tags = []
    
    try:
        # NebulaGraph 返回结果通常可以通过 as_primitive 或类似方法转换
        if hasattr(result, 'column_values'):
            # nebula5-python 格式
            for row in result.rows():
                if hasattr(row, 'values') and len(row.values) > 0:
                    tag_name = row.values[0].get_sVal()
                    if isinstance(tag_name, bytes):
                        tag_name = tag_name.decode('utf-8')
                    tags.append(tag_name)
        elif hasattr(result, 'as_primitive'):
            # 尝试 as_primitive 方法
            data = result.as_primitive()
            for row in data:
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    tags.append(str(row[0]))
    except Exception as e:
        log(f"解析 SHOW TAGS 结果失败: {e}")
    
    return tags


def _parse_show_edges(result: Any) -> List[str]:
    """解析 SHOW EDGES 的结果"""
    edges = []
    
    try:
        if hasattr(result, 'column_values'):
            for row in result.rows():
                if hasattr(row, 'values') and len(row.values) > 0:
                    edge_name = row.values[0].get_sVal()
                    if isinstance(edge_name, bytes):
                        edge_name = edge_name.decode('utf-8')
                    edges.append(edge_name)
        elif hasattr(result, 'as_primitive'):
            data = result.as_primitive()
            for row in data:
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    edges.append(str(row[0]))
    except Exception as e:
        log(f"解析 SHOW EDGES 结果失败: {e}")
    
    return edges


def _read_tag_schema(client: Any, tag_name: str) -> Optional[VertexSchema]:
    """
    读取 TAG 的 schema
    
    DESCRIBE TAG 返回格式（示例）：
    +----------+----------+----------+---------+---------+
    | Field    | Type     | Null     | Default | Comment |
    +----------+----------+----------+---------+---------+
    | "id"     | "int64"  | "NO"     |         |         |
    | "name"   | "string" | "YES"    |         |         |
    +----------+----------+----------+---------+---------+
    """
    try:
        result = client.execute(f"DESCRIBE TAG {tag_name}")
        properties = _parse_describe_result(result)
        
        return VertexSchema(
            label=tag_name,
            properties=properties
        )
    except Exception as e:
        log(f"读取 TAG {tag_name} schema 失败: {e}")
        return None


def _read_edge_schema(client: Any, edge_name: str) -> Optional[EdgeSchema]:
    """
    读取 EDGE 的 schema
    
    DESCRIBE EDGE 返回格式与 DESCRIBE TAG 相同
    """
    try:
        result = client.execute(f"DESCRIBE EDGE {edge_name}")
        properties = _parse_describe_result(result)
        
        return EdgeSchema(
            label=edge_name,
            properties=properties
        )
    except Exception as e:
        log(f"读取 EDGE {edge_name} schema 失败: {e}")
        return None


def _parse_describe_result(result: Any) -> List[PropertySchema]:
    """
    解析 DESCRIBE TAG/EDGE 的结果
    
    返回字段列表，每个字段包含：name, type, nullable
    """
    properties = []
    
    try:
        if hasattr(result, 'column_values'):
            # nebula5-python 格式
            for row in result.rows():
                if hasattr(row, 'values') and len(row.values) >= 3:
                    # Field, Type, Null, Default, Comment
                    field_name = row.values[0].get_sVal()
                    field_type = row.values[1].get_sVal()
                    nullable_str = row.values[2].get_sVal()
                    
                    if isinstance(field_name, bytes):
                        field_name = field_name.decode('utf-8')
                    if isinstance(field_type, bytes):
                        field_type = field_type.decode('utf-8')
                    if isinstance(nullable_str, bytes):
                        nullable_str = nullable_str.decode('utf-8')
                    
                    nullable = nullable_str.upper() == "YES"
                    
                    properties.append(PropertySchema(
                        name=field_name,
                        type=field_type,
                        nullable=nullable
                    ))
        elif hasattr(result, 'as_primitive'):
            # 尝试 as_primitive 方法
            data = result.as_primitive()
            for row in data:
                if isinstance(row, (list, tuple)) and len(row) >= 3:
                    field_name = str(row[0])
                    field_type = str(row[1])
                    nullable_str = str(row[2])
                    nullable = nullable_str.upper() == "YES"
                    
                    properties.append(PropertySchema(
                        name=field_name,
                        type=field_type,
                        nullable=nullable
                    ))
    except Exception as e:
        log(f"解析 DESCRIBE 结果失败: {e}")
    
    return properties
