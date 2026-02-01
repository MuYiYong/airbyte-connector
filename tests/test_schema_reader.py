"""
测试 Schema Reader 模块
"""
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from yueshu_airbyte_connector.schema_reader import (
    PropertySchema,
    VertexSchema,
    EdgeSchema,
    GraphSchema
)


def test_property_schema():
    """测试属性 schema"""
    prop = PropertySchema(name="id", type="int64", nullable=False)
    assert prop.name == "id"
    assert prop.type == "int64"
    assert not prop.nullable
    print("✓ PropertySchema 测试通过")


def test_vertex_schema():
    """测试点类型 schema"""
    props = [
        PropertySchema(name="id", type="int64", nullable=False),
        PropertySchema(name="name", type="string", nullable=True),
    ]
    vertex = VertexSchema(label="Actor", properties=props)
    
    assert vertex.label == "Actor"
    assert len(vertex.properties) == 2
    assert vertex.get_property("id").type == "int64"
    assert vertex.get_property("name").type == "string"
    assert vertex.get_property("nonexist") is None
    print("✓ VertexSchema 测试通过")


def test_edge_schema():
    """测试边类型 schema"""
    props = [
        PropertySchema(name="roleName", type="string", nullable=True),
    ]
    edge = EdgeSchema(label="Act", properties=props)
    
    assert edge.label == "Act"
    assert len(edge.properties) == 1
    assert edge.get_property("roleName").type == "string"
    print("✓ EdgeSchema 测试通过")


def test_graph_schema():
    """测试图 schema"""
    vertex1 = VertexSchema(label="Actor", properties=[])
    vertex2 = VertexSchema(label="Movie", properties=[])
    edge1 = EdgeSchema(label="Act", properties=[])
    
    graph = GraphSchema(
        graph_name="movie",
        vertices={"Actor": vertex1, "Movie": vertex2},
        edges={"Act": edge1}
    )
    
    assert graph.graph_name == "movie"
    assert len(graph.vertices) == 2
    assert len(graph.edges) == 1
    assert graph.get_vertex_schema("Actor") == vertex1
    assert graph.get_edge_schema("Act") == edge1
    assert graph.get_vertex_schema("nonexist") is None
    print("✓ GraphSchema 测试通过")


if __name__ == "__main__":
    print("开始测试 Schema Reader 模块...")
    test_property_schema()
    test_vertex_schema()
    test_edge_schema()
    test_graph_schema()
    print("\n✅ 所有测试通过!")
