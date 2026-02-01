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
    读取 Yueshu 5.2.0 图的完整 schema
    
    使用 DESC GRAPH 命令查询 graph type，然后用 DESC GRAPH TYPE 命令获取完整的 schema 信息
    
    Args:
        client: NebulaClient 实例
        graph_name: 图空间名称
        
    Returns:
        GraphSchema 实例
    """
    schema = GraphSchema(graph_name=graph_name)
    
    try:
        log(f"正在读取图 {graph_name} 的 schema...")
        
        # Step 1: 获取 graph 的 type
        graph_type = _get_graph_type(client, graph_name)
        if not graph_type:
            log(f"无法获取图 {graph_name} 的 type")
            return schema
        
        log(f"图 {graph_name} 的类型: {graph_type}")
        
        # Step 2: 使用 DESC GRAPH TYPE 获取完整的 schema
        graph_schema_info = _read_graph_type_schema(client, graph_type)
        
        # Step 3: 解析顶点和边的 schema
        for entity_type, entity_name, labels, properties, primary_or_multi_key in graph_schema_info:
            if entity_type == "Node":
                vertex_schema = VertexSchema(label=entity_name)
                # 从属性列表推断数据类型（默认为 string）
                for prop_name in properties:
                    vertex_schema.properties.append(PropertySchema(
                        name=prop_name,
                        type="string",  # Yueshu 的 schema 不提供类型信息，默认为 string
                        nullable=True
                    ))
                # 标记主键属性
                if primary_or_multi_key:
                    for key_name in primary_or_multi_key:
                        prop = vertex_schema.get_property(key_name)
                        if prop:
                            prop.nullable = False  # 主键不为空
                schema.vertices[entity_name] = vertex_schema
                log(f"  顶点 {entity_name}: {len(vertex_schema.properties)} 个属性")
                


def _parse_show_tags(result: Any) -> List[str]:
    """
    解析 SHOW TAGS 的结果（弃用）
    
    现在使用 DESC GRAPH TYPE 代替
    """
    tags = []
    try:
        if hasattr(result, 'column_values'):
            for row in result.rows():
                if hasattr(row, 'values') and len(row.values) > 0:
                    tag_name = row.values[0].get_sVal()
                    if isinstance(tag_name, bytes):
                        tag_name = tag_name.decode('utf-8')
                    tags.append(tag_name)
        elif hasattr(result, 'as_primitive'):
            data = result.as_primitive()
            for row in data:
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    tags.append(str(row[0]))
    except Exception as e:
        log(f"解析 SHOW TAGS 结果失败: {e}")
    return tags
