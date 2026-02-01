#!/usr/bin/env python3
"""
探索 Yueshu 5.2.0 的 schema 读取命令
"""

import sys
sys.path.insert(0, '/Users/muyi/Documents/Vesoft/workspace/airbyte-connector/src')

from yueshu_airbyte_connector.nebula_client import NebulaClient
from yueshu_airbyte_connector.common import log


def test_yueshu_schema_commands():
    """测试 DESC GRAPH 和 DESC GRAPH TYPE 命令"""
    try:
        # 连接到实际的 Yueshu 服务
        client = NebulaClient(
            hosts=["192.168.15.240:39669"],
            username="root",
            password="Nebula123",
            graph=None
        )
        
        client.connect()
        log("✅ 成功连接到 Yueshu 服务 (192.168.15.240:39669)")
        
        # 列出所有 graph
        log("\n=== 列出所有 GRAPH ===")
        result = client.execute("SHOW GRAPHS")
        log(f"SHOW GRAPHS 结果: {result}")
        if hasattr(result, 'rows'):
            for row in result.rows():
                log(f"  行数据: {row}")
                if hasattr(row, 'values'):
                    for i, val in enumerate(row.values):
                        log(f"    值 {i}: {val} (类型: {type(val).__name__})")
                        if hasattr(val, 'get_sVal'):
                            log(f"      get_sVal(): {val.get_sVal()}")
        
        # 使用 as_primitive 解析
        log("\n=== 使用 as_primitive 解析 SHOW GRAPHS ===")
        result = client.execute("SHOW GRAPHS")
        if hasattr(result, 'as_primitive_by_row'):
            for row_data in result.as_primitive_by_row():
                log(f"  行: {row_data}")
        elif hasattr(result, 'as_primitive'):
            all_data = result.as_primitive()
            log(f"  所有数据: {all_data}")
        
        # 获取 Tron graph 的信息
        log("\n=== DESC GRAPH Tron ===")
        result = client.execute("DESC GRAPH Tron")
        log(f"DESC GRAPH Tron 结果类型: {type(result).__name__}")
        log(f"结果: {result}")
        
        # 使用 as_primitive_by_row 解析
        log("\n=== 使用 as_primitive_by_row 解析 ===")
        result = client.execute("DESC GRAPH Tron")
        graph_type = None
        if hasattr(result, 'as_primitive_by_row'):
            for row_data in result.as_primitive_by_row():
                log(f"  行: {row_data}")
                # row_data 是字典格式
                if isinstance(row_data, dict):
                    graph_type = row_data.get('graph_type_name')
                    log(f"  提取的 graph_type: {graph_type}")
                elif isinstance(row_data, (list, tuple)) and len(row_data) >= 2:
                    graph_type = row_data[1]
                    log(f"  提取的 graph_type: {graph_type}")
        elif hasattr(result, 'as_primitive'):
            data = result.as_primitive()
            log(f"  as_primitive: {data}")
        elif hasattr(result, 'rows'):
            log("行数据:")
            for row in result.rows():
                log(f"  {row}")
                if hasattr(row, 'values'):
                    for i, val in enumerate(row.values):
                        log(f"    值 {i}: {val} (类型: {type(val).__name__})")
                        if hasattr(val, 'get_sVal'):
                            log(f"      get_sVal(): {val.get_sVal()}")
        elif hasattr(result, 'column_names'):
            log(f"列名: {result.column_names}")
        
        if graph_type:
            log(f"Graph type: {graph_type}")
            
            # 描述 graph type
            log(f"\n=== DESC GRAPH TYPE {graph_type} ===")
            result = client.execute(f"DESC GRAPH TYPE {graph_type}")
            log(f"结果类型: {type(result).__name__}")
            
            # 使用 as_primitive_by_row 解析
            if hasattr(result, 'as_primitive_by_row'):
                log("行数据（字典格式）:")
                for i, row_data in enumerate(result.as_primitive_by_row()):
                    log(f"\n  行 {i}:")
                    for key, value in row_data.items():
                        log(f"    {key}: {value} (类型: {type(value).__name__})")
            elif hasattr(result, 'rows'):
                log("行数据:")
                for i, row in enumerate(result.rows()):
                    log(f"  行 {i}: {row}")
                    if hasattr(row, 'values'):
                        for j, val in enumerate(row.values):
                            log(f"    列 {j}: {val} (类型: {type(val).__name__})")
                            if hasattr(val, 'get_sVal'):
                                log(f"      get_sVal(): {val.get_sVal()}")
                            elif hasattr(val, 'get_iVal'):
                                log(f"      get_iVal(): {val.get_iVal()}")
            elif hasattr(result, 'column_names'):
                log(f"列名: {result.column_names}")
        
        log("\n✅ 命令测试完成")
        
    except Exception as e:
        log(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_yueshu_schema_commands()
    sys.exit(0 if success else 1)
