#!/usr/bin/env python3
"""测试实际的 Nebula Graph 连接"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from yueshu_airbyte_connector.nebula_client import NebulaClient, NebulaClientError

# 测试配置
HOST = "192.168.15.240:39669"
USERNAME = "root"
PASSWORD = "Nebula123"

print("=" * 60)
print("测试 Nebula Graph 连接")
print("=" * 60)
print(f"Host: {HOST}")
print(f"Username: {USERNAME}")
print("=" * 60)

client = NebulaClient(
    hosts=[HOST],
    username=USERNAME,
    password=PASSWORD,
)

try:
    print("\n1. 连接到服务器...")
    client.connect()
    print("✅ 连接成功")
    
    print("\n2. 测试基本查询 (RETURN 1 AS a, 2 AS b)...")
    result = client.execute("RETURN 1 AS a, 2 AS b")
    print(f"✅ 查询成功")
    print(f"Result: {client.result_to_payload(result)}")
    
    print("\n3. 查看当前用户...")
    result = client.execute("SHOW CURRENT_USER")
    print(f"✅ 查询成功")
    print(f"Current user: {client.result_to_payload(result)}")
    
    print("\n4. 查看所有图空间...")
    result = client.execute("SHOW SPACES")
    print(f"✅ 查询成功")
    print(f"Spaces: {client.result_to_payload(result)}")
    
    # 如果有图空间，尝试使用第一个
    if hasattr(result, "as_primitive_by_row"):
        rows = list(result.as_primitive_by_row())
        if rows:
            # 获取第一个图空间的名称
            first_space = rows[0]
            if isinstance(first_space, dict) and 'Name' in first_space:
                space_name = first_space['Name']
                print(f"\n5. 尝试切换到图空间: {space_name}")
                result = client.execute(f"USE {space_name}")
                print(f"✅ 切换成功")
                
                print(f"\n6. 查看图空间 {space_name} 的标签...")
                result = client.execute("SHOW TAGS")
                print(f"✅ 查询成功")
                print(f"Tags: {client.result_to_payload(result)}")
                
                print(f"\n7. 查看图空间 {space_name} 的边类型...")
                result = client.execute("SHOW EDGES")
                print(f"✅ 查询成功")
                print(f"Edges: {client.result_to_payload(result)}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过")
    print("=" * 60)
    
except NebulaClientError as e:
    print(f"\n❌ Nebula 客户端错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\n❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    print("\n8. 关闭连接...")
    client.close()
    print("✅ 连接已关闭")
