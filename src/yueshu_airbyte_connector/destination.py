from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Optional

from .common import (
    DEFAULT_CHECK_QUERY,
    emit_message,
    iter_airbyte_messages,
    log,
    read_catalog_from_env,
    to_destination_config,
)
from .gql_generator import (
    generate_gql_from_mapping,
    generate_vertex_gql_with_schema,
    generate_edge_gql_with_schema,
    transform_flat_config_to_mapping,
)
from .nebula_client import NebulaClient, NebulaClientError
from .schema_reader import GraphSchema, read_graph_schema


def spec() -> Dict[str, Any]:
    return {
        "type": "SPEC",
        "spec": {
            "documentationUrl": "",
            "connectionSpecification": {
                "type": "object",
                "required": ["hosts", "username", "password"],
                "properties": {
                    "hosts": {"type": "array", "items": {"type": "string"}},
                    "username": {"type": "string", "default": "root"},
                    "password": {"type": "string", "airbyte_secret": True, "default": "root"},
                    "graph": {"type": "string", "description": "The graph space to connect to.", "default": ""},
                },
            },
            "supportsNormalization": False,
            "supportsDBT": False,
            "supported_destination_sync_modes": ["append", "overwrite"],
        },
    }


def check(config_data: Dict[str, Any]) -> None:
    cfg = to_destination_config(config_data)
    client = NebulaClient(
        hosts=cfg.hosts,
        username=cfg.username,
        password=cfg.password,
    )
    try:
        client.connect()
        client.execute(DEFAULT_CHECK_QUERY)
        
        # 如果配置了 graph，尝试读取 schema
        if cfg.graph:
            log(f"正在验证图空间 {cfg.graph}...")
            try:
                schema = read_graph_schema(client, cfg.graph)
                log(f"成功读取 schema: {len(schema.vertices)} 个点类型, {len(schema.edges)} 个边类型")
            except Exception as e:
                emit_message(
                    {
                        "type": "CONNECTION_STATUS",
                        "connectionStatus": {
                            "status": "FAILED",
                            "message": f"无法读取图空间 {cfg.graph} 的 schema: {e}"
                        },
                    }
                )
                return
        
        emit_message(
            {
                "type": "CONNECTION_STATUS",
                "connectionStatus": {"status": "SUCCEEDED"},
            }
        )
    except NebulaClientError as exc:
        emit_message(
            {
                "type": "CONNECTION_STATUS",
                "connectionStatus": {"status": "FAILED", "message": str(exc)},
            }
        )
    finally:
        client.close()


def discover(config_data: Dict[str, Any]) -> None:
    """
    Discover the graph schema and return catalog with streams for each vertex and edge type.
    
    For Yueshu, this generates streams for:
    - Each vertex type (e.g., Account, User, etc.)
    - Each edge type (e.g., Transfer, follows, etc.)
    """
    cfg = to_destination_config(config_data)
    
    if not cfg.graph:
        emit_message(
            {
                "type": "CATALOG",
                "catalog": {"streams": []},
            }
        )
        return
    
    client = NebulaClient(
        hosts=cfg.hosts,
        username=cfg.username,
        password=cfg.password,
    )
    
    try:
        client.connect()
        
        # 读取 graph schema
        schema = read_graph_schema(client, cfg.graph)
        
        streams = []
        
        # 为每个顶点类型创建 stream
        for vertex_label, vertex_schema in schema.vertices.items():
            stream_def = {
                "name": vertex_label,
                "json_schema": {
                    "type": "object",
                    "properties": {
                        prop.name: {
                            "type": "string" if prop.type == "string" else "number",
                            "description": f"{prop.name} (类型: {prop.type})",
                        }
                        for prop in vertex_schema.properties
                    },
                    "required": [
                        prop.name for prop in vertex_schema.properties 
                        if not prop.nullable
                    ],
                },
                "supported_destination_sync_modes": ["append", "overwrite"],
                "default_cursor_field": [],
            }
            # 为 destination 包装 stream 和初始配置
            stream = {
                "stream": stream_def,
                "config": {
                    "destination_sync_mode": "append",  # 默认选择 append 模式
                    "tag": vertex_label,  # 指定要写入的顶点类型
                    "field_mapping": {},  # 空映射表示使用默认映射
                }
            }
            streams.append(stream)
            log(f"发现顶点类型: {vertex_label} (属性: {len(vertex_schema.properties)})")
        
        # 为每个边类型创建 stream
        for edge_label, edge_schema in schema.edges.items():
            stream_def = {
                "name": edge_label,
                "json_schema": {
                    "type": "object",
                    "properties": {
                        prop.name: {
                            "type": "string" if prop.type == "string" else "number",
                            "description": f"{prop.name} (类型: {prop.type})",
                        }
                        for prop in edge_schema.properties
                    },
                    "required": [
                        prop.name for prop in edge_schema.properties 
                        if not prop.nullable
                    ],
                },
                "supported_destination_sync_modes": ["append", "overwrite"],
                "default_cursor_field": [],
            }
            # 为 destination 包装 stream 和初始配置
            stream = {
                "stream": stream_def,
                "config": {
                    "destination_sync_mode": "append",  # 默认选择 append 模式
                    "edge": edge_label,  # 指定要写入的边类型
                    "field_mapping": {},  # 空映射表示使用默认映射
                }
            }
            streams.append(stream)
            log(f"发现边类型: {edge_label} (属性: {len(edge_schema.properties)})")
        
        emit_message(
            {
                "type": "CATALOG",
                "catalog": {"streams": streams},
            }
        )
        log(f"成功发现 {len(streams)} 个 streams")
        
    except Exception as e:
        log(f"discover 操作失败: {e}")
        import traceback
        traceback.print_exc()
        emit_message(
            {
                "type": "CATALOG",
                "catalog": {"streams": []},
            }
        )
    finally:
        client.close()



_WRITE_MODE_MAP = {
    # Airbyte sync modes 映射到 Yueshu INSERT 语句
    "append": "INSERT OR IGNORE",  # append: 只插入新数据，忽略重复的主键
    "overwrite": "INSERT OR REPLACE",  # overwrite: 覆盖已有数据
    # 也支持直接指定 Yueshu 的语句类型
    "insert": "INSERT",
    "insert or replace": "INSERT OR REPLACE",
    "insert or ignore": "INSERT OR IGNORE",
    "insert or update": "INSERT OR UPDATE",
}


def _normalize_write_mode(write_mode: str | None) -> str:
    """
    将 Airbyte sync mode 或 Yueshu INSERT 语句类型转换为对应的 INSERT 关键字
    
    映射关系：
    - "append" (Airbyte sync mode)       → "INSERT OR IGNORE"  (只插入新数据，忽略重复)
    - "overwrite" (Airbyte sync mode)    → "INSERT OR REPLACE" (覆盖已有数据)
    - 或直接使用 Yueshu 的语句类型（insert, insert or replace 等）
    
    默认值: "INSERT OR IGNORE" （保守的追加模式）
    """
    if not write_mode:
        return _WRITE_MODE_MAP["append"]  # 默认使用 INSERT OR IGNORE (append 模式)
    normalized = write_mode.strip().lower()
    return _WRITE_MODE_MAP.get(normalized, _WRITE_MODE_MAP["append"])


def _replace_first_insert(query: str, insert_keyword: str) -> str:
    return re.sub(r"\binsert\b", insert_keyword, query, count=1, flags=re.IGNORECASE)


def _apply_table_insert(query: str, write_mode: str | None) -> str:
    insert_keyword = _normalize_write_mode(write_mode)
    stripped = query.lstrip()
    upper = stripped.upper()

    if upper.startswith("TABLE "):
        if "INSERT" in upper:
            return _replace_first_insert(stripped, insert_keyword)
        return stripped

    if upper.startswith("MATCH "):
        if "INSERT" in upper:
            return f"TABLE {_replace_first_insert(stripped, insert_keyword)}"
        return f"TABLE {stripped}"

    if "INSERT" in upper:
        replaced = _replace_first_insert(stripped, insert_keyword)
        return f"TABLE {replaced}"

    return query


def _load_write_map(config_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Load write configuration from catalog.
    Supports three mapping formats (in priority order):
    1. Schema-based (new) - tag/edge + field_mapping
    2. Mapping-based (hierarchical) - full mapping config
    3. Mapping-based (flat) - auto-converted to hierarchical
    """
    catalog = read_catalog_from_env() or {}
    write_map: Dict[str, Dict[str, Any]] = {}

    for stream_entry in catalog.get("streams", []):
        stream_info = stream_entry.get("stream") or stream_entry
        name = stream_info.get("name")
        if not name:
            continue
        
        config = stream_entry.get("config") or {}
        
        # Priority 1: Check for schema-based configuration (new format)
        if "tag" in config or "edge" in config:
            # 新的基于 schema 的配置
            write_map[name] = {
                "mode": "schema_based",
                "tag": config.get("tag"),
                "edge": config.get("edge"),
                "src_tag": config.get("src_tag"),
                "dst_tag": config.get("dst_tag"),
                "field_mapping": config.get("field_mapping", {}),
                "setup_queries": config.get("setup_queries") or [],
            }
            continue
        
        # Priority 2: Check for mapping-based configuration (hierarchical format)
        if "mapping" in config:
            write_map[name] = {
                "mode": "mapping_based",
                "mapping_config": {
                    "graph": config.get("graph"),
                    "mapping": config["mapping"],
                    "write_mode": config.get("write_mode", "insert or ignore"),
                },
                "graph": config.get("graph"),
                "setup_queries": config.get("setup_queries") or [],
            }
            continue
        
        # Priority 3: Check for flat mapping configuration
        if "mapping_type" in config:
            # Transform flat config to standard mapping format
            mapping_config = transform_flat_config_to_mapping(config)
            write_map[name] = {
                "mode": "mapping_based",
                "mapping_config": mapping_config,
                "graph": config.get("graph"),
                "setup_queries": config.get("setup_queries") or [],
            }
            continue

    return write_map


def write(config_data: Dict[str, Any], stdin: Iterable[str]) -> None:
    cfg = to_destination_config(config_data)
    write_map = _load_write_map(config_data)
    if not write_map:
        raise ValueError(
            "配置不能为空，请在 AIRBYTE_CATALOG 的 stream config 中提供配置"
        )
    
    client = NebulaClient(
        hosts=cfg.hosts,
        username=cfg.username,
        password=cfg.password,
    )
    
    # 读取 schema（如果需要）
    schema: Optional[GraphSchema] = None
    if cfg.graph:
        try:
            client.connect()
            schema = read_graph_schema(client, cfg.graph)
            log(f"成功读取 graph {cfg.graph} schema: {len(schema.vertices)} 点类型, {len(schema.edges)} 边类型")
        except Exception as e:
            log(f"读取 schema 失败: {e}")
            client.close()
            raise ValueError(f"无法读取图空间 {cfg.graph} 的 schema: {e}")
    else:
        client.connect()
    
    # 获取全局 insert_mode
    global_insert_mode = cfg.insert_mode
    
    try:
        current_graph = cfg.graph if cfg.graph else None
        initialized_streams = set()
        
        for message in iter_airbyte_messages(stdin):
            if message.get("type") != "RECORD":
                continue
            
            record = message.get("record", {})
            stream = record.get("stream")
            data = record.get("data", {})
            write_item = write_map.get(stream)
            
            if not write_item:
                continue
            
            # Handle graph switching (for backward compatibility with old config)
            graph = write_item.get("graph") or current_graph
            if graph and graph != current_graph:
                client.execute(f"USE {graph}")
                current_graph = graph
            
            # Execute setup queries once per stream
            if stream not in initialized_streams:
                for query in write_item.get("setup_queries") or []:
                    if query:
                        client.execute(query)
                initialized_streams.add(stream)
            
            # Generate GQL based on configuration mode
            mode = write_item.get("mode", "mapping_based")
            
            if mode == "schema_based":
                # 新的基于 schema 的配置
                if not schema:
                    raise ValueError(f"未配置 graph，无法使用 schema-based 模式 (stream: {stream})")
                
                tag = write_item.get("tag")
                edge = write_item.get("edge")
                field_mapping = write_item.get("field_mapping", {})
                
                try:
                    if tag:
                        # 点表插入
                        tag_schema = schema.get_vertex_schema(tag)
                        if not tag_schema:
                            raise ValueError(f"TAG {tag} 在 schema 中不存在")
                        gql = generate_vertex_gql_with_schema(tag_schema, field_mapping, data)
                        write_mode = global_insert_mode
                    elif edge:
                        # 边表插入
                        edge_schema = schema.get_edge_schema(edge)
                        if not edge_schema:
                            raise ValueError(f"EDGE {edge} 在 schema 中不存在")
                        
                        src_tag = write_item.get("src_tag")
                        dst_tag = write_item.get("dst_tag")
                        if not src_tag or not dst_tag:
                            raise ValueError(f"Edge 配置缺少 src_tag 或 dst_tag (stream: {stream})")
                        
                        gql = generate_edge_gql_with_schema(
                            edge_schema, src_tag, dst_tag, field_mapping, data
                        )
                        write_mode = global_insert_mode
                    else:
                        raise ValueError(f"schema-based 配置必须指定 tag 或 edge (stream: {stream})")
                except Exception as e:
                    log(f"生成 GQL 失败: {e}, stream={stream}, data={data}")
                    raise ValueError(f"GQL 生成失败 (stream: {stream}): {e}")
                    
            else:
                # 旧的 mapping-based 配置（向后兼容）
                mapping_config = write_item.get("mapping_config", {})
                try:
                    gql = generate_gql_from_mapping(mapping_config, data)
                    write_mode = mapping_config.get("write_mode") or global_insert_mode
                except Exception as e:
                    log(f"生成 GQL 失败: {e}, stream={stream}, data={data}")
                    raise ValueError(f"GQL 生成失败 (stream: {stream}): {e}")
            
            # Apply write mode
            gql = _apply_table_insert(gql, write_mode)
            
            log(f"写入流 {stream}: {gql}")
            client.execute(gql)
        
        emit_message({"type": "STATE", "state": {"last_write": True}})
    finally:
        client.close()
