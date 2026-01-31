#!/usr/bin/env python3
"""
测试 GQL 生成器功能
验证 mapping 配置能正确生成 GQL 语句
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from yueshu_airbyte_connector.gql_generator import (
    generate_gql_from_mapping,
    transform_flat_config_to_mapping,
)


def test_vertex_mapping():
    """测试点表映射"""
    print("=" * 60)
    print("测试 1: 点表映射（Vertex Mapping）")
    print("=" * 60)
    
    mapping_config = {
        "graph": "movie",
        "mapping": {
            "type": "vertex",
            "label": "Actor",
            "primary_key": {
                "source_field": "id",
                "dest_field": "id"
            },
            "properties": [
                {"source_field": "name", "dest_field": "name"},
                {"source_field": "birth_date", "dest_field": "birthDate", "transform": "date"}
            ]
        },
        "write_mode": "insert or replace"
    }
    
    record = {
        "id": 1001,
        "name": "Tom Hanks",
        "birth_date": "1956-07-09"
    }
    
    gql = generate_gql_from_mapping(mapping_config, record)
    print(f"配置: {mapping_config['mapping']['label']} 点")
    print(f"记录: {record}")
    print(f"生成 GQL:\n{gql}\n")
    
    expected = 'INSERT (@Actor{id: 1001, name: "Tom Hanks", birthDate: date("1956-07-09")})'
    assert gql == expected, f"GQL不匹配!\n期望: {expected}\n实际: {gql}"
    print("✅ 测试通过\n")


def test_edge_mapping():
    """测试边表映射"""
    print("=" * 60)
    print("测试 2: 边表映射（Edge Mapping）")
    print("=" * 60)
    
    mapping_config = {
        "graph": "movie",
        "mapping": {
            "type": "edge",
            "label": "Act",
            "src_vertex": {
                "label": "Actor",
                "primary_key": {
                    "source_field": "actor_id",
                    "dest_field": "id"
                }
            },
            "dst_vertex": {
                "label": "Movie",
                "primary_key": {
                    "source_field": "movie_id",
                    "dest_field": "id"
                }
            },
            "multiedge_key": {"source_field": "role_id"},
            "properties": [
                {"source_field": "role_name", "dest_field": "roleName"}
            ]
        },
        "write_mode": "insert or update"
    }
    
    record = {
        "actor_id": 1001,
        "movie_id": 2001,
        "role_id": 1,
        "role_name": "Forrest Gump"
    }
    
    gql = generate_gql_from_mapping(mapping_config, record)
    print(f"配置: {mapping_config['mapping']['label']} 边")
    print(f"记录: {record}")
    print(f"生成 GQL:\n{gql}\n")
    
    assert "MATCH" in gql, "边映射应包含 MATCH 子句"
    assert "@Actor" in gql, "应包含 Actor 类型"
    assert "@Movie" in gql, "应包含 Movie 类型"
    assert "@Act" in gql, "应包含 Act 边类型"
    assert ":1" in gql, "应包含多边键"
    assert "roleName" in gql, "应包含边属性"
    print("✅ 测试通过\n")


def test_flat_config_conversion():
    """测试扁平配置转换"""
    print("=" * 60)
    print("测试 3: 扁平配置转换（Flat Config Transformation）")
    print("=" * 60)
    
    flat_config = {
        "graph": "movie",
        "mapping_type": "vertex",
        "label": "Actor",
        "primary_key_source": "id",
        "primary_key_dest": "id",
        "properties_mapping": '[{"source_field":"name","dest_field":"name"}]'
    }
    
    converted = transform_flat_config_to_mapping(flat_config)
    print(f"扁平配置: {flat_config}")
    print(f"转换结果: {converted}\n")
    
    assert converted["mapping"]["type"] == "vertex"
    assert converted["mapping"]["label"] == "Actor"
    assert converted["mapping"]["primary_key"]["source_field"] == "id"
    assert len(converted["mapping"]["properties"]) == 1
    print("✅ 测试通过\n")


def test_edge_without_multiedge_key():
    """测试无多边键的边表映射"""
    print("=" * 60)
    print("测试 4: 无多边键的边表映射")
    print("=" * 60)
    
    mapping_config = {
        "graph": "movie",
        "mapping": {
            "type": "edge",
            "label": "Follow",
            "src_vertex": {
                "label": "Person",
                "primary_key": {
                    "source_field": "follower_id",
                    "dest_field": "id"
                }
            },
            "dst_vertex": {
                "label": "Person",
                "primary_key": {
                    "source_field": "followee_id",
                    "dest_field": "id"
                }
            }
        }
    }
    
    record = {
        "follower_id": 100,
        "followee_id": 200
    }
    
    gql = generate_gql_from_mapping(mapping_config, record)
    print(f"记录: {record}")
    print(f"生成 GQL:\n{gql}\n")
    
    assert "MATCH" in gql
    assert "@Follow" in gql
    # 不应该有 ranking/multiedge key
    assert ":1" not in gql and ":0" not in gql
    print("✅ 测试通过\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GQL 生成器测试套件")
    print("=" * 60 + "\n")
    
    try:
        test_vertex_mapping()
        test_edge_mapping()
        test_flat_config_conversion()
        test_edge_without_multiedge_key()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
