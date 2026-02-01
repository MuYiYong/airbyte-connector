#!/usr/bin/env python3
"""
测试 write mode 的映射是否正确
"""

import sys
sys.path.insert(0, '/Users/muyi/Documents/Vesoft/workspace/airbyte-connector/src')

from yueshu_airbyte_connector.destination import _normalize_write_mode, _WRITE_MODE_MAP, _apply_table_insert

print("="*70)
print("Write Mode 映射测试")
print("="*70)

# 测试 1: 检查映射表
print("\n✅ 1. Write Mode 映射表:")
for key, value in _WRITE_MODE_MAP.items():
    print(f"   {key:25} → {value}")

# 测试 2: 测试 normalize_write_mode
print("\n✅ 2. _normalize_write_mode 函数测试:")
test_cases = [
    (None, "INSERT OR IGNORE", "默认值 (append 模式)"),
    ("", "INSERT OR IGNORE", "空字符串 (append 模式)"),
    ("append", "INSERT OR IGNORE", "Airbyte append mode"),
    ("APPEND", "INSERT OR IGNORE", "Airbyte append mode (大写)"),
    ("overwrite", "INSERT OR REPLACE", "Airbyte overwrite mode"),
    ("OVERWRITE", "INSERT OR REPLACE", "Airbyte overwrite mode (大写)"),
    ("insert", "INSERT", "Yueshu INSERT"),
    ("INSERT OR REPLACE", "INSERT OR REPLACE", "Yueshu INSERT OR REPLACE"),
    ("insert or ignore", "INSERT OR IGNORE", "Yueshu INSERT OR IGNORE"),
    ("insert or update", "INSERT OR UPDATE", "Yueshu INSERT OR UPDATE"),
]

all_pass = True
for input_mode, expected, description in test_cases:
    result = _normalize_write_mode(input_mode)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_pass = False
    print(f"   {status} {description:45} {input_mode!r:25} → {result}")

# 测试 3: 测试 apply_table_insert
print("\n✅ 3. _apply_table_insert 函数测试:")
query_tests = [
    ("TABLE INSERT INTO Account (address) VALUES ('test')", "append", "TABLE INSERT OR IGNORE INTO Account (address) VALUES ('test')"),
    ("TABLE INSERT INTO Account (address) VALUES ('test')", "overwrite", "TABLE INSERT OR REPLACE INTO Account (address) VALUES ('test')"),
    ("INSERT INTO Account (address) VALUES ('test')", "append", "TABLE INSERT OR IGNORE INTO Account (address) VALUES ('test')"),
    ("MATCH (v) INSERT INTO Account (address) VALUES ('test')", "overwrite", "TABLE MATCH (v) INSERT OR REPLACE INTO Account (address) VALUES ('test')"),
]

for query, mode, expected in query_tests:
    result = _apply_table_insert(query, mode)
    # 简化比较，因为可能有空格差异
    status = "✅" if result.upper() == expected.upper() else "❌"
    if result.upper() != expected.upper():
        all_pass = False
    print(f"   {status} Mode: {mode:10} {query[:40]:40} → ...")

print("\n" + "="*70)
if all_pass:
    print("🎉 所有 Write Mode 映射测试通过！")
else:
    print("⚠️  有些映射测试失败")
print("="*70)

# 总结
print("\n📋 映射关系总结:")
print("   Airbyte 'append'    → Yueshu INSERT OR IGNORE  (保留现有数据，新数据忽略)")
print("   Airbyte 'overwrite' → Yueshu INSERT OR REPLACE (覆盖现有数据)")
print("\n💡 这样确保用户在 Airbyte UI 中选择的同步模式能正确映射到")
print("   Yueshu 图数据库支持的 INSERT 语句类型。")
