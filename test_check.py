#!/usr/bin/env python3
"""测试 CHECK 操作以诊断连接问题"""

import sys
import json
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from yueshu_airbyte_connector.destination import check
from yueshu_airbyte_connector.common import to_destination_config

# 测试配置
test_config = {
    "hosts": ["127.0.0.1:9669"],
    "username": "root",
    "password": "root",
    "graph": ""  # 留空或填写实际的 graph
}

print("=" * 60)
print("测试 CHECK 操作")
print("=" * 60)
print(f"配置: {json.dumps(test_config, indent=2)}")
print("=" * 60)

try:
    check(test_config)
    print("\n✅ CHECK 操作成功完成")
except Exception as e:
    print(f"\n❌ CHECK 操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
