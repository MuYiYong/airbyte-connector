#!/usr/bin/env python3
"""
测试 schema_reader 是否能正确读取 Yueshu 图的 schema
"""

import sys
sys.path.insert(0, '/Users/muyi/Documents/Vesoft/workspace/airbyte-connector/src')

from yueshu_airbyte_connector.nebula_client import NebulaClient
from yueshu_airbyte_connector.schema_reader import read_graph_schema
from yueshu_airbyte_connector.common import log


def test_schema_reader():
    """测试 schema 读取"""
    try:
        # 连接到 Yueshu
        client = NebulaClient(
            hosts=["127.0.0.1"],
            username="root",
            password="nebula",
            graph=None  # 不设置默认图空间
        )
        
        log("✅ 连接成功")
        
        # 调用 connect() 初始化客户端
        client.connect()
        log("✅ 客户端初始化成功")
        
        # 测试读取默认图 Tron 的 schema
        schema = read_graph_schema(client, "Tron")
        log(f"✅ 成功读取 Tron 的 schema")
        log(f"   - 点类型数: {len(schema.vertices)}")
        log(f"   - 边类型数: {len(schema.edges)}")
        
        if schema.vertices:
            log(f"   - 点类型: {list(schema.vertices.keys())}")
            for label, vertex in schema.vertices.items():
                log(f"      {label}: {len(vertex.properties)} 个属性")
        
        if schema.edges:
            log(f"   - 边类型: {list(schema.edges.keys())}")
            for label, edge in schema.edges.items():
                log(f"      {label}: {len(edge.properties)} 个属性")
        
        log("✅ 所有 schema 读取测试通过！")
        
    except Exception as e:
        log(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_schema_reader()
    sys.exit(0 if success else 1)
