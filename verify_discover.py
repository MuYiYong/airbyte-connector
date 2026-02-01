#!/usr/bin/env python3
"""
验证 discover 输出的格式是否符合 Airbyte 规范
"""

import json
import subprocess
import sys

# 运行 discover 命令
result = subprocess.run(
    [
        "docker", "run", "--rm", "-v", f"{sys.path[0]}:/workspace",
        "yueshu-connector:test",
        "--connector-type", "destination",
        "discover", "--config", "/workspace/test_config_schema.json"
    ],
    capture_output=True,
    text=True,
    cwd="/Users/muyi/Documents/Vesoft/workspace/airbyte-connector"
)

# 提取 JSON 消息
lines = result.stdout.strip().split('\n')
json_lines = [line for line in lines if line.strip().startswith('{')]

if not json_lines:
    print("❌ 未找到 JSON 输出")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    sys.exit(1)

# 解析最后一个 JSON（应该是 CATALOG 消息）
catalog_json = json_lines[-1]
catalog = json.loads(catalog_json)

print("✅ Discover 输出:")
print(json.dumps(catalog, indent=2))

# 验证必要字段
if catalog.get("type") != "CATALOG":
    print("❌ 消息类型不是 CATALOG")
    sys.exit(1)

if "catalog" not in catalog:
    print("❌ 缺少 catalog 字段")
    sys.exit(1)

streams = catalog["catalog"].get("streams", [])
print(f"\n✅ 找到 {len(streams)} 个 streams")

# 验证每个 stream 的必要字段
required_stream_fields = {"name", "json_schema", "supported_destination_sync_modes"}

for i, stream in enumerate(streams):
    stream_name = stream.get("name", "UNKNOWN")
    print(f"\n Stream {i+1}: {stream_name}")
    
    # 检查必要字段
    missing = required_stream_fields - set(stream.keys())
    if missing:
        print(f"  ❌ 缺少字段: {missing}")
    else:
        print(f"  ✅ 包含所有必要字段")
    
    # 检查 sync modes
    sync_modes = stream.get("supported_destination_sync_modes", [])
    print(f"  Sync modes: {sync_modes}")
    
    # 检查 json_schema
    json_schema = stream.get("json_schema", {})
    props = json_schema.get("properties", {})
    print(f"  Properties: {list(props.keys())}")
    
    required_props = json_schema.get("required", [])
    print(f"  Required: {required_props}")

print("\n✅ 验证完成")
