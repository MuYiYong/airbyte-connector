# Yueshu 5.2.0 Schema 读取实现指南

## 概述

本文档详细说明了如何在 Yueshu 5.2.0 中正确读取 Graph 的 Schema 信息。

## Yueshu 5.2.0 Schema 查询命令

### 1. DESC GRAPH - 获取 Graph 信息

```sql
DESC GRAPH <graph_name>
```

**返回列：**
- `graph_name`: 图空间名称
- `graph_type_name`: 图的类型名称

**示例输出：**
```
graph_name: 'Tron'
graph_type_name: 'blockchain'
```

**Python 代码解析：**
```python
result = client.execute("DESC GRAPH Tron")
if hasattr(result, 'as_primitive_by_row'):
    for row_data in result.as_primitive_by_row():
        if isinstance(row_data, dict):
            graph_type = row_data.get('graph_type_name')  # 'blockchain'
```

### 2. DESC GRAPH TYPE - 获取完整 Schema

```sql
DESC GRAPH TYPE <graph_type_name>
```

**返回列：**
- `entity_type`: "Node" 或 "Edge"
- `type_name`: 实体类型名（如 Account, Transfer）
- `type_pattern`: 实体的模式表达式
- `labels`: 标签列表（数组格式）
- `properties`: 属性名列表（数组格式）
- `primary_key/multiedge_key`: 主键/多边键列表（数组格式）

**示例输出：**
```json
[
  {
    "entity_type": "Node",
    "type_name": "Account",
    "type_pattern": "(Account)",
    "labels": ["Account"],
    "properties": ["address", "entity_label", "risk_label", "in_degree", "out_degree", "in_sum", "out_sum"],
    "primary_key/multiedge_key": ["address"]
  },
  {
    "entity_type": "Edge",
    "type_name": "Transfer",
    "type_pattern": "(Account)-[Transfer]->(Account)",
    "labels": ["Transfer"],
    "properties": ["token_address", "first_time", "last_time", "sum", "tx_count"],
    "primary_key/multiedge_key": ["token_address"]
  }
]
```

**Python 代码解析：**
```python
result = client.execute("DESC GRAPH TYPE blockchain")
if hasattr(result, 'as_primitive_by_row'):
    for row_data in result.as_primitive_by_row():
        if isinstance(row_data, dict):
            entity_type = row_data.get('entity_type')  # "Node" 或 "Edge"
            type_name = row_data.get('type_name')      # "Account" 或 "Transfer"
            properties = row_data.get('properties')    # ['address', ...]
            primary_key = row_data.get('primary_key/multiedge_key')  # ['address']
```

## 关键点

### 不支持的命令

Yueshu 5.2.0 **不支持**以下命令：
- ❌ `USE <graph_name>` - 不能用于切换图空间
- ❌ `OPEN GRAPH <graph_name>`
- ❌ `SHOW TAGS` - 需要在 graph context 中执行，但无法设置 context
- ❌ `SHOW EDGES`
- ❌ `DESCRIBE TAG` / `DESCRIBE EDGE`

### ResultSet 解析方法

使用 `as_primitive_by_row()` 方法获取字典格式的结果：

```python
result = client.execute("DESC GRAPH Tron")

# ✅ 正确的方法
if hasattr(result, 'as_primitive_by_row'):
    for row_data in result.as_primitive_by_row():
        if isinstance(row_data, dict):
            # 使用字典访问
            graph_type = row_data.get('graph_type_name')
```

## Airbyte 连接器实现

### 完整的 Schema 读取流程

```python
def read_graph_schema(client: Any, graph_name: str) -> GraphSchema:
    """
    读取 Yueshu 5.2.0 图的完整 schema
    """
    schema = GraphSchema(graph_name=graph_name)
    
    # Step 1: 获取 graph 的 type
    result = client.execute(f"DESC GRAPH {graph_name}")
    graph_type = None
    for row_data in result.as_primitive_by_row():
        if isinstance(row_data, dict):
            graph_type = row_data.get('graph_type_name')
    
    if not graph_type:
        return schema
    
    # Step 2: 使用 DESC GRAPH TYPE 获取完整的 schema
    result = client.execute(f"DESC GRAPH TYPE {graph_type}")
    
    # Step 3: 解析顶点和边的 schema
    for row_data in result.as_primitive_by_row():
        if isinstance(row_data, dict):
            entity_type = row_data.get('entity_type')
            type_name = row_data.get('type_name')
            properties = row_data.get('properties', [])
            primary_key = row_data.get('primary_key/multiedge_key', [])
            
            if entity_type == "Node":
                vertex = VertexSchema(label=type_name)
                for prop in properties:
                    vertex.properties.append(PropertySchema(
                        name=prop,
                        type="string",  # Yueshu 不提供类型信息
                        nullable=prop not in primary_key
                    ))
                schema.vertices[type_name] = vertex
            
            elif entity_type == "Edge":
                edge = EdgeSchema(label=type_name)
                for prop in properties:
                    edge.properties.append(PropertySchema(
                        name=prop,
                        type="string",
                        nullable=prop not in primary_key
                    ))
                schema.edges[type_name] = edge
    
    return schema
```

## 测试结果

✅ Yueshu 服务连接成功 (192.168.15.240:39669)
✅ DESC GRAPH 命令执行成功
✅ DESC GRAPH TYPE 命令执行成功
✅ Airbyte check 操作通过

输出示例：
```
正在验证图空间 Tron...
正在读取图 Tron 的 schema...
图 Tron 的类型: blockchain
  顶点 Account: 7 个属性
  边 Transfer: 5 个属性
成功读取 schema: 1 个点类型, 1 个边类型
{"type": "CONNECTION_STATUS", "connectionStatus": {"status": "SUCCEEDED"}}
```

## 代码文件修改

修改的文件：
- `src/yueshu_airbyte_connector/schema_reader.py` - 完全重写 schema 读取逻辑，使用 DESC GRAPH 和 DESC GRAPH TYPE 命令

关键函数：
- `read_graph_schema(client, graph_name)` - 主入口函数，负责完整的 schema 读取
- `_get_graph_type(client, graph_name)` - 获取 graph 的 type
- `_read_graph_type_schema(client, graph_type)` - 读取 graph type 的完整 schema

## 数据类型说明

⚠️ **重要提示：** Yueshu 5.2.0 的 DESC GRAPH TYPE 命令不提供属性的具体数据类型信息。
因此，所有属性都默认映射为 `string` 类型。在实际使用中，如需精确的类型信息，建议：

1. 查阅 Yueshu 的图定义文档
2. 从实际数据推断类型
3. 在 Airbyte 的数据映射中指定具体类型

## 参考资源

- Yueshu 5.2.0 GQL 语言文档：/Users/muyi/Downloads/yueshu-graph-5.2.0
- nebula5-python 文档：https://github.com/vesoft-inc/nebula-python/tree/v5.2.1
