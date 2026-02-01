#!/usr/bin/env python3
"""
完整的 Airbyte destination connector 验证测试
"""

import json
import subprocess
import sys

def run_command(command):
    """运行 Docker 命令并返回输出"""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd="/Users/muyi/Documents/Vesoft/workspace/airbyte-connector"
    )
    return result.stdout, result.stderr, result.returncode

def test_spec():
    """测试 spec 命令"""
    print("\n" + "="*60)
    print("测试 1: SPEC 命令")
    print("="*60)
    
    cmd = [
        "docker", "run", "--rm",
        "yueshu-connector:test",
        "--connector-type", "destination", "spec"
    ]
    
    stdout, stderr, code = run_command(cmd)
    
    if code != 0:
        print(f"❌ SPEC 命令失败: {stderr}")
        return False
    
    try:
        spec = json.loads(stdout.strip())
        print(f"✅ SPEC 命令成功")
        print(f"   - 类型: {spec.get('type')}")
        print(f"   - Sync Modes: {spec['spec'].get('supported_destination_sync_modes')}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return False

def test_check():
    """测试 check 命令"""
    print("\n" + "="*60)
    print("测试 2: CHECK 命令")
    print("="*60)
    
    cmd = [
        "docker", "run", "--rm", "-v", f"{sys.path[0]}:/workspace",
        "yueshu-connector:test",
        "--connector-type", "destination",
        "check", "--config", "/workspace/test_config_schema.json"
    ]
    
    stdout, stderr, code = run_command(cmd)
    
    if code != 0:
        print(f"❌ CHECK 命令失败: {stderr}")
        return False
    
    # 查找 JSON 行
    json_lines = [line for line in stdout.split('\n') if line.strip().startswith('{')]
    
    if not json_lines:
        print(f"❌ 未找到 JSON 输出")
        return False
    
    try:
        result = json.loads(json_lines[-1])
        if result.get("type") == "CONNECTION_STATUS":
            status = result.get("connectionStatus", {}).get("status")
            if status == "SUCCEEDED":
                print(f"✅ CHECK 命令成功")
                print(f"   - 连接状态: {status}")
                return True
            else:
                print(f"❌ 连接失败: {status}")
                return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return False

def test_discover():
    """测试 discover 命令"""
    print("\n" + "="*60)
    print("测试 3: DISCOVER 命令")
    print("="*60)
    
    cmd = [
        "docker", "run", "--rm", "-v", f"{sys.path[0]}:/workspace",
        "yueshu-connector:test",
        "--connector-type", "destination",
        "discover", "--config", "/workspace/test_config_schema.json"
    ]
    
    stdout, stderr, code = run_command(cmd)
    
    if code != 0:
        print(f"❌ DISCOVER 命令失败: {stderr}")
        return False
    
    # 查找 JSON 行
    json_lines = [line for line in stdout.split('\n') if line.strip().startswith('{')]
    
    if not json_lines:
        print(f"❌ 未找到 JSON 输出")
        return False
    
    try:
        result = json.loads(json_lines[-1])
        if result.get("type") == "CATALOG":
            streams = result.get("catalog", {}).get("streams", [])
            print(f"✅ DISCOVER 命令成功")
            print(f"   - 发现的 Streams: {len(streams)}")
            
            for stream in streams:
                name = stream.get("name")
                sync_modes = stream.get("supported_destination_sync_modes", [])
                props = stream.get("json_schema", {}).get("properties", {})
                print(f"     * {name}: {len(props)} 个属性, Sync Modes: {sync_modes}")
            
            return True
        else:
            print(f"❌ 消息类型不是 CATALOG: {result.get('type')}")
            return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("Yueshu Airbyte Destination Connector 完整验证")
    print("="*60)
    
    results = {
        "SPEC": test_spec(),
        "CHECK": test_check(),
        "DISCOVER": test_discover(),
    }
    
    print("\n" + "="*60)
    print("验证总结")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} {status}")
    
    all_passed = all(results.values())
    print("\n" + ("="*60))
    if all_passed:
        print("🎉 所有测试通过！连接器已准备就绪")
    else:
        print("⚠️  有些测试失败，请检查错误日志")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
