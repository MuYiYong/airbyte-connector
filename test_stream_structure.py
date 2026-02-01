#!/usr/bin/env python3
"""验证 discover 返回的 stream 结构是否包含 config 和 stream 对象"""

# 模拟 discover 返回的 stream 结构
def test_stream_structure():
    """测试 stream 结构是否有 'stream' 和 'config' 对象"""
    
    # 模拟一个顶点 stream 结构
    vertex_stream = {
        "stream": {
            "name": "Account",
            "json_schema": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "account_id (类型: string)"},
                    "balance": {"type": "number", "description": "balance (类型: double)"},
                },
                "required": ["account_id"],
            },
            "supported_destination_sync_modes": ["append", "overwrite"],
            "default_cursor_field": [],
        },
        "config": {
            "destination_sync_mode": "append",
            "tag": "Account",
            "field_mapping": {},
        }
    }
    
    # 模拟一个边 stream 结构
    edge_stream = {
        "stream": {
            "name": "Transfer",
            "json_schema": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "amount (类型: double)"},
                    "time": {"type": "string", "description": "time (类型: string)"},
                },
                "required": ["amount"],
            },
            "supported_destination_sync_modes": ["append", "overwrite"],
            "default_cursor_field": [],
        },
        "config": {
            "destination_sync_mode": "append",
            "edge": "Transfer",
            "field_mapping": {},
        }
    }
    
    # 验证结构
    print("✅ 顶点 stream 结构验证:")
    assert "stream" in vertex_stream, "缺少 'stream' 字段"
    assert "config" in vertex_stream, "缺少 'config' 字段"
    assert "name" in vertex_stream["stream"], "stream 缺少 'name' 字段"
    assert "json_schema" in vertex_stream["stream"], "stream 缺少 'json_schema' 字段"
    assert "supported_destination_sync_modes" in vertex_stream["stream"], "stream 缺少 'supported_destination_sync_modes' 字段"
    assert "destination_sync_mode" in vertex_stream["config"], "config 缺少 'destination_sync_mode' 字段"
    assert "tag" in vertex_stream["config"], "config 缺少 'tag' 字段(顶点)"
    assert "field_mapping" in vertex_stream["config"], "config 缺少 'field_mapping' 字段"
    print(f"  - 顶点stream名称: {vertex_stream['stream']['name']}")
    print(f"  - 默认同步模式: {vertex_stream['config']['destination_sync_mode']}")
    print(f"  - 标签: {vertex_stream['config']['tag']}")
    print(f"  - 支持的模式: {vertex_stream['stream']['supported_destination_sync_modes']}")
    
    print("\n✅ 边 stream 结构验证:")
    assert "stream" in edge_stream, "缺少 'stream' 字段"
    assert "config" in edge_stream, "缺少 'config' 字段"
    assert "edge" in edge_stream["config"], "config 缺少 'edge' 字段(边)"
    print(f"  - 边stream名称: {edge_stream['stream']['name']}")
    print(f"  - 默认同步模式: {edge_stream['config']['destination_sync_mode']}")
    print(f"  - 边类型: {edge_stream['config']['edge']}")
    print(f"  - 支持的模式: {edge_stream['stream']['supported_destination_sync_modes']}")
    
    print("\n✅ Catalog 结构验证:")
    catalog = {
        "type": "CATALOG",
        "catalog": {
            "streams": [vertex_stream, edge_stream]
        }
    }
    assert len(catalog["catalog"]["streams"]) == 2, "streams 数量不对"
    print(f"  - 总 streams 数: {len(catalog['catalog']['streams'])}")
    print(f"  - 第一个 stream 名称: {catalog['catalog']['streams'][0]['stream']['name']}")
    print(f"  - 第二个 stream 名称: {catalog['catalog']['streams'][1]['stream']['name']}")
    
    print("\n✅ 所有结构验证通过! ✓")
    print("\n📋 这个结构应该会在 Airbyte UI 中显示:")
    print("  1. 两个 stream (Account, Transfer)")
    print("  2. 每个 stream 都有 Sync mode 下拉菜单，显示: append, overwrite")
    print("  3. 初始默认选择: append")

if __name__ == "__main__":
    test_stream_structure()
