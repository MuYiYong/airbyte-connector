"""
GQL 生成工具：根据 mapping 配置自动生成 GQL 语句
"""
from typing import Any, Dict, List
import json


def transform_flat_config_to_mapping(flat_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    将扁平化的 stream config 转换为标准的 mapping 结构
    
    Args:
        flat_config: Airbyte UI 扁平化配置
        
    Returns:
        标准的 mapping 配置
    """
    mapping_type = flat_config.get("mapping_type", "vertex")
    
    if mapping_type == "vertex":
        mapping = {
            "type": "vertex",
            "label": flat_config.get("label", ""),
            "primary_key": {
                "source_field": flat_config.get("primary_key_source", ""),
                "dest_field": flat_config.get("primary_key_dest", "id")
            }
        }
    else:  # edge
        mapping = {
            "type": "edge",
            "label": flat_config.get("label", ""),
            "src_vertex": {
                "label": flat_config.get("src_vertex_label", ""),
                "primary_key": {
                    "source_field": flat_config.get("primary_key_source", ""),
                    "dest_field": flat_config.get("primary_key_dest", "id")
                }
            },
            "dst_vertex": {
                "label": flat_config.get("dst_vertex_label", ""),
                "primary_key": {
                    "source_field": flat_config.get("dst_primary_key_source", ""),
                    "dest_field": flat_config.get("dst_primary_key_dest", "id")
                }
            }
        }
        
        # 多边键（可选）
        multiedge_field = flat_config.get("multiedge_key_field")
        if multiedge_field:
            mapping["multiedge_key"] = {"source_field": multiedge_field}
    
    # 属性映射
    properties_json = flat_config.get("properties_mapping", "[]")
    try:
        properties = json.loads(properties_json) if isinstance(properties_json, str) else properties_json
        if properties:
            mapping["properties"] = properties
    except json.JSONDecodeError:
        mapping["properties"] = []
    
    return {
        "graph": flat_config.get("graph", ""),
        "mapping": mapping,
        "write_mode": flat_config.get("write_mode", "insert or ignore")
    }


def generate_gql_from_mapping(mapping_config: Dict[str, Any], record: Dict[str, Any]) -> str:
    """
    根据 mapping 配置和记录数据生成 GQL 语句
    
    Args:
        mapping_config: Mapping 配置
        record: 数据记录
        
    Returns:
        GQL 语句
    """
    mapping = mapping_config.get("mapping", {})
    mapping_type = mapping.get("type", "vertex")
    
    if mapping_type == "vertex":
        return _generate_vertex_gql(mapping, record)
    else:
        return _generate_edge_gql(mapping, record)


def _generate_vertex_gql(mapping: Dict[str, Any], record: Dict[str, Any]) -> str:
    """生成点插入 GQL"""
    label = mapping.get("label", "")
    pk = mapping.get("primary_key", {})
    properties = mapping.get("properties", [])
    
    # 构建属性列表
    attrs = []
    
    # 主键
    pk_source = pk.get("source_field", "")
    pk_dest = pk.get("dest_field", "id")
    if pk_source in record:
        attrs.append(f"{pk_dest}: {_format_value(record[pk_source])}")
    
    # 其他属性
    for prop in properties:
        source_field = prop.get("source_field", "")
        dest_field = prop.get("dest_field", "")
        transform = prop.get("transform", "")
        
        if source_field in record:
            value = record[source_field]
            formatted = _apply_transform(value, transform)
            attrs.append(f"{dest_field}: {formatted}")
    
    attrs_str = ", ".join(attrs)
    return f"INSERT (@{label}{{{attrs_str}}})"


def _generate_edge_gql(mapping: Dict[str, Any], record: Dict[str, Any]) -> str:
    """生成边插入 GQL"""
    label = mapping.get("label", "")
    src = mapping.get("src_vertex", {})
    dst = mapping.get("dst_vertex", {})
    multiedge = mapping.get("multiedge_key", {})
    properties = mapping.get("properties", [])
    
    # 构建 MATCH 子句
    src_label = src.get("label", "")
    src_pk_source = src.get("primary_key", {}).get("source_field", "")
    src_pk_dest = src.get("primary_key", {}).get("dest_field", "id")
    
    dst_label = dst.get("label", "")
    dst_pk_source = dst.get("primary_key", {}).get("source_field", "")
    dst_pk_dest = dst.get("primary_key", {}).get("dest_field", "id")
    
    src_pk_val = _format_value(record.get(src_pk_source, ""))
    dst_pk_val = _format_value(record.get(dst_pk_source, ""))
    
    match_clause = f"MATCH (src@{src_label}{{{src_pk_dest}: {src_pk_val}}}), "
    match_clause += f"(dst@{dst_label}{{{dst_pk_dest}: {dst_pk_val}}})"
    
    # 多边键
    ranking = ""
    if multiedge and "source_field" in multiedge:
        ranking_field = multiedge["source_field"]
        if ranking_field in record:
            ranking = f":{record[ranking_field]}"
    
    # 边属性
    attrs = []
    for prop in properties:
        source_field = prop.get("source_field", "")
        dest_field = prop.get("dest_field", "")
        transform = prop.get("transform", "")
        
        if source_field in record:
            value = record[source_field]
            formatted = _apply_transform(value, transform)
            attrs.append(f"{dest_field}: {formatted}")
    
    attrs_str = ", ".join(attrs) if attrs else ""
    edge_clause = f"(src)-[@{label}{ranking}{{{attrs_str}}}]->(dst)"
    
    return f"{match_clause} INSERT {edge_clause}"


def _format_value(value: Any) -> str:
    """格式化值"""
    if isinstance(value, str):
        # 转义双引号
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif value is None:
        return "NULL"
    else:
        return str(value)


def _apply_transform(value: Any, transform: str) -> str:
    """应用类型转换"""
    if not transform:
        return _format_value(value)
    
    if transform == "date":
        return f'date("{value}")'
    elif transform == "datetime":
        return f'datetime("{value}")'
    elif transform == "timestamp":
        return f'timestamp("{value}")'
    else:
        return _format_value(value)


# 测试代码
if __name__ == "__main__":
    # 测试点表 GQL 生成
    vertex_config = {
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
    
    vertex_record = {
        "id": 1001,
        "name": "Tom Hanks",
        "birth_date": "1956-07-09"
    }
    
    vertex_gql = generate_gql_from_mapping(vertex_config, vertex_record)
    print("点表 GQL:")
    print(vertex_gql)
    print()
    
    # 测试边表 GQL 生成
    edge_config = {
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
    
    edge_record = {
        "actor_id": 1001,
        "movie_id": 2001,
        "role_id": 1,
        "role_name": "Forrest Gump"
    }
    
    edge_gql = generate_gql_from_mapping(edge_config, edge_record)
    print("边表 GQL:")
    print(edge_gql)
    print()
    
    # 测试扁平化配置转换
    flat_config = {
        "graph": "movie",
        "mapping_type": "vertex",
        "label": "Actor",
        "primary_key_source": "id",
        "primary_key_dest": "id",
        "properties_mapping": '[{"source_field":"name","dest_field":"name"},{"source_field":"birth_date","dest_field":"birthDate","transform":"date"}]'
    }
    
    converted_config = transform_flat_config_to_mapping(flat_config)
    print("扁平化配置转换:")
    print(json.dumps(converted_config, indent=2, ensure_ascii=False))
