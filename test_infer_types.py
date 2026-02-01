#!/usr/bin/env python3
"""
尝试从实际数据查询来推断数据类型
"""

import sys
sys.path.insert(0, '/Users/muyi/Documents/Vesoft/workspace/airbyte-connector/src')

from yueshu_airbyte_connector.nebula_client import NebulaClient
from yueshu_airbyte_connector.common import log


def test_infer_types():
    """从实际数据推断数据类型"""
    try:
        # 连接到实际的 Yueshu 服务
        client = NebulaClient(
            hosts=["192.168.15.240:39669"],
            username="root",
            password="Nebula123",
            graph="Tron"  # 直接连接到 Tron graph
        )
        
        client.connect()
        log("✅ 成功连接到 Tron 图")
        
        # 尝试一个简单的查询
        log("\n=== 查询 Account 顶点示例 ===")
        query = "MATCH (v:Account) RETURN v LIMIT 1"
        result = client.execute(query)
        log(f"结果: {result}")
        
        if hasattr(result, 'as_primitive_by_row'):
            for row_data in result.as_primitive_by_row():
                log(f"行: {row_data}")
                for key, value in row_data.items():
                    log(f"  {key}: {value} (类型: {type(value).__name__})")
        
        # 尝试查询属性
        log("\n=== 查询 Account 属性 ===")
        query = "MATCH (v:Account) RETURN v.address, v.entity_label, v.in_degree LIMIT 1"
        result = client.execute(query)
        log(f"列名: {result.column_names if hasattr(result, 'column_names') else 'N/A'}")
        
        if hasattr(result, 'as_primitive_by_row'):
            for row_data in result.as_primitive_by_row():
                log(f"行: {row_data}")
                for key, value in row_data.items():
                    log(f"  {key}: {value} (Python类型: {type(value).__name__})")
        
        log("\n✅ 查询测试完成")
        
    except Exception as e:
        log(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_infer_types()
    sys.exit(0 if success else 1)
