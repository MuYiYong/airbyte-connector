#!/usr/bin/env python3
"""
探索 DESCRIBE VERTEX 和 DESCRIBE EDGE 命令获取属性详情
"""

import sys
sys.path.insert(0, '/Users/muyi/Documents/Vesoft/workspace/airbyte-connector/src')

from yueshu_airbyte_connector.nebula_client import NebulaClient
from yueshu_airbyte_connector.common import log


def test_describe_vertex_edge():
    """测试 DESCRIBE VERTEX 和 DESCRIBE EDGE 命令"""
    try:
        # 连接到实际的 Yueshu 服务
        client = NebulaClient(
            hosts=["192.168.15.240:39669"],
            username="root",
            password="Nebula123",
            graph=None
        )
        
        client.connect()
        log("✅ 成功连接到 Yueshu 服务")
        
        # 测试可能的命令变体
        commands_to_test = [
            "SHOW VERTEX LABELS",
            "SHOW EDGE LABELS",
            "SHOW TAGS",
            "SHOW EDGES",
            "FETCH PROP ON Account 1",
        ]
        
        for cmd in commands_to_test:
            log(f"\n=== {cmd} ===")
            try:
                result = client.execute(cmd)
                log(f"成功! 结果: {result}")
                if hasattr(result, 'column_names'):
                    log(f"列名: {result.column_names}")
                if hasattr(result, 'as_primitive_by_row'):
                    rows = list(result.as_primitive_by_row())
                    log(f"行数 (前 3 行):")
                    for row in rows[:3]:
                        log(f"  {row}")
            except Exception as e:
                log(f"失败: {e}")
        
        log("\n✅ 命令测试完成")
        
    except Exception as e:
        log(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_describe_vertex_edge()
    sys.exit(0 if success else 1)
