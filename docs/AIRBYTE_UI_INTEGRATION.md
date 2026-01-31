# Airbyte UI 集成指南

本文档提供三种集成方案，将可视化映射配置 UI 集成到 Airbyte 中。

---

## 方案对比

| 方案 | 复杂度 | 开发时间 | 灵活度 | 推荐度 |
|------|--------|----------|--------|--------|
| **方案一：JSON Schema + 原生 UI** | ⭐ 低 | 1-2天 | ⭐⭐ | ⭐⭐⭐⭐⭐ 最推荐 |
| **方案二：自定义 React 组件** | ⭐⭐⭐ 高 | 2-3周 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ 适合深度定制 |
| **方案三：插件化 UI** | ⭐⭐ 中 | 1周 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ 平衡方案 |

---

## 方案一：JSON Schema + Airbyte 原生 UI（推荐）

### 优势
- ✅ **最简单**：无需修改 Airbyte 源码
- ✅ **快速上线**：只需修改 connector 代码
- ✅ **官方支持**：使用 Airbyte 标准 JSON Schema
- ✅ **自动生成 UI**：Airbyte 根据 schema 自动渲染表单

### 实现步骤

#### Step 1: 更新 Connector Spec

修改 `src/yueshu_airbyte_connector/destination.py` 的 `spec()` 函数：

```python
import json
from pathlib import Path

def spec() -> Dict[str, Any]:
    """返回 connector 规范，包括 connection spec 和 stream config spec"""
    
    # 加载 connection specification (connector 级别配置)
    connection_spec = _load_spec("destination_spec.json")
    
    return {
        "type": "SPEC",
        "spec": {
            "documentationUrl": "https://github.com/your-org/yueshu-airbyte-connector",
            "connectionSpecification": connection_spec,
            # 关键：添加 stream-level configuration schema
            "supportsNormalization": False,
            "supportsDBT": False,
            "supported_destination_sync_modes": ["append", "overwrite"],
        },
    }

def _load_spec(filename: str) -> Dict[str, Any]:
    """加载 JSON 规范文件"""
    spec_dir = Path(__file__).parent.parent.parent / "specs"
    spec_path = spec_dir / filename
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)
```

#### Step 2: 在 Catalog 中定义 Stream Config Schema

Airbyte 支持在 **Catalog discovery** 时为每个 stream 提供配置 schema。修改您的 connector 以支持 `discover` 命令（如果还没有）：

```python
def discover(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    发现可用的 streams 并为每个 stream 提供配置 schema
    """
    # 加载 stream 配置 schema
    stream_config_schema = _load_spec("stream_config_ui_spec.json")
    
    return {
        "type": "CATALOG",
        "catalog": {
            "streams": [
                {
                    "stream": {
                        "name": "default_stream",
                        "json_schema": {},  # 源数据的 schema
                        "supported_sync_modes": ["full_refresh", "incremental"],
                    },
                    # 关键：为这个 stream 提供配置表单 schema
                    "config": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        **stream_config_schema
                    }
                }
            ]
        }
    }
```

#### Step 3: 简化 Stream Config Schema

由于 Airbyte 的原生 UI 对复杂嵌套结构支持有限，我们需要**扁平化** schema：

创建 `specs/stream_config_flat_spec.json`：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["graph", "mapping_type"],
  "properties": {
    "graph": {
      "type": "string",
      "title": "图空间",
      "order": 0
    },
    "mapping_type": {
      "type": "string",
      "title": "映射类型",
      "enum": ["vertex", "edge"],
      "order": 1
    },
    "label": {
      "type": "string",
      "title": "类型标签（点类型或边类型）",
      "order": 2
    },
    "primary_key_source": {
      "type": "string",
      "title": "主键：源表字段",
      "description": "点表：主键字段；边表：起点主键字段",
      "order": 3
    },
    "primary_key_dest": {
      "type": "string",
      "title": "主键：目标字段",
      "order": 4
    },
    "src_vertex_label": {
      "type": "string",
      "title": "边：起点类型",
      "description": "仅边表需要",
      "order": 5
    },
    "dst_vertex_label": {
      "type": "string",
      "title": "边：终点类型",
      "order": 6
    },
    "dst_primary_key_source": {
      "type": "string",
      "title": "边：终点主键源字段",
      "order": 7
    },
    "dst_primary_key_dest": {
      "type": "string",
      "title": "边：终点主键目标字段",
      "order": 8
    },
    "multiedge_key_field": {
      "type": "string",
      "title": "边：多边键字段（可选）",
      "order": 9
    },
    "properties_mapping": {
      "type": "string",
      "title": "属性映射（JSON 格式）",
      "description": "格式: [{\"source_field\":\"name\",\"dest_field\":\"name\",\"transform\":\"\"},{...}]",
      "order": 10,
      "default": "[]"
    },
    "write_mode": {
      "type": "string",
      "title": "写入模式",
      "enum": ["insert", "insert or replace", "insert or ignore", "insert or update"],
      "default": "insert or ignore",
      "order": 11
    }
  }
}
```

#### Step 4: 添加配置转换逻辑

在 `destination.py` 中添加转换函数，将扁平化的 UI 配置转换为内部使用的结构：

```python
def _transform_flat_config_to_mapping(flat_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    将扁平化的 stream config 转换为标准的 mapping 结构
    """
    mapping_type = flat_config.get("mapping_type", "vertex")
    
    if mapping_type == "vertex":
        mapping = {
            "type": "vertex",
            "label": flat_config.get("label", ""),
            "primary_key": {
                "source_field": flat_config.get("primary_key_source", ""),
                "dest_field": flat_config.get("primary_key_dest", "")
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
                    "dest_field": flat_config.get("primary_key_dest", "")
                }
            },
            "dst_vertex": {
                "label": flat_config.get("dst_vertex_label", ""),
                "primary_key": {
                    "source_field": flat_config.get("dst_primary_key_source", ""),
                    "dest_field": flat_config.get("dst_primary_key_dest", "")
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
        pass
    
    return {
        "graph": flat_config.get("graph", ""),
        "mapping": mapping,
        "write_mode": flat_config.get("write_mode", "insert or ignore")
    }
```

#### Step 5: 生成 GQL 语句

添加根据 mapping 配置自动生成 GQL 的函数：

```python
def _generate_gql_from_mapping(mapping_config: Dict[str, Any], record: Dict[str, Any]) -> str:
    """
    根据 mapping 配置和记录数据生成 GQL 语句
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
    pk_dest = pk.get("dest_field", "")
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
    src_pk_dest = src.get("primary_key", {}).get("dest_field", "")
    
    dst_label = dst.get("label", "")
    dst_pk_source = dst.get("primary_key", {}).get("source_field", "")
    dst_pk_dest = dst.get("primary_key", {}).get("dest_field", "")
    
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
        return f'"{value}"'
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
```

#### Step 6: 更新 Write 函数

修改 `_load_write_map` 函数以支持新的 mapping 配置：

```python
def _load_write_map(config_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    catalog = read_catalog_from_env() or {}
    write_map: Dict[str, Dict[str, Any]] = {}

    for stream_entry in catalog.get("streams", []):
        stream_info = stream_entry.get("stream") or stream_entry
        name = stream_info.get("name")
        if not name:
            continue
        
        config = stream_entry.get("config") or {}
        
        # 新方式：使用 mapping 配置
        if "mapping" in config or "mapping_type" in config:
            # 如果是扁平化配置，先转换
            if "mapping_type" in config and "mapping" not in config:
                config = _transform_flat_config_to_mapping(config)
            
            write_map[name] = {
                "use_mapping": True,
                "mapping_config": config,
                "graph": config.get("graph"),
                "write_mode": config.get("write_mode"),
            }
        # 旧方式：使用手写的 query template
        else:
            template = config.get("write_query_template") or config.get("query_template")
            if template:
                write_map[name] = {
                    "use_mapping": False,
                    "query_template": template,
                    "write_mode": config.get("write_mode"),
                    "graph": config.get("graph"),
                    "setup_queries": config.get("setup_queries") or [],
                }

    return write_map
```

修改 `write` 函数以使用新的 GQL 生成逻辑：

```python
def write(config_data: Dict[str, Any], stdin: Iterable[str]) -> None:
    cfg = to_destination_config(config_data)
    write_map = _load_write_map(config_data)
    if not write_map:
        raise ValueError("需要配置 stream mapping")
    
    client = NebulaClient(
        hosts=cfg.hosts,
        username=cfg.username,
        password=cfg.password,
    )
    
    try:
        client.connect()
        current_graph = None
        
        for message in iter_airbyte_messages(stdin):
            if message.get("type") != "RECORD":
                continue
            
            record = message.get("record", {})
            stream = record.get("stream")
            data = record.get("data", {})
            
            write_item = write_map.get(stream)
            if not write_item:
                continue
            
            # 切换图空间
            graph = write_item.get("graph")
            if graph and graph != current_graph:
                client.execute(f"SESSION SET GRAPH {graph}")
                current_graph = graph
            
            # 生成并执行 GQL
            if write_item.get("use_mapping"):
                # 新方式：根据 mapping 生成 GQL
                mapping_config = write_item.get("mapping_config", {})
                gql = _generate_gql_from_mapping(mapping_config, data)
            else:
                # 旧方式：使用模板
                gql = _apply_template(write_item.get("query_template", ""), data)
            
            # 应用 write mode
            gql = _apply_table_insert(gql, write_item.get("write_mode"))
            
            log(f"执行 GQL: {gql[:100]}...")
            client.execute(gql)
        
        emit_message({"type": "STATE", "state": {"last_write": True}})
    
    finally:
        client.close()
```

---

## 方案二：开发自定义 React 组件

如果您需要更高级的 UI 定制，可以直接在 Airbyte 前端添加自定义组件。

### 实现步骤

#### Step 1: Fork Airbyte 仓库

```bash
git clone https://github.com/airbytehq/airbyte.git
cd airbyte
```

#### Step 2: 创建自定义组件

在 `airbyte-webapp/src/components/connector/` 下创建新组件：

```bash
mkdir -p airbyte-webapp/src/components/connector/YueshuDestination
```

创建 `YueshuStreamConfig.tsx`：

```typescript
import React, { useState } from 'react';
import { useField } from 'formik';

interface StreamConfigProps {
  streamName: string;
  streamFields: string[];
}

export const YueshuStreamConfig: React.FC<StreamConfigProps> = ({
  streamName,
  streamFields
}) => {
  const [field, , helpers] = useField(`streams.${streamName}.config`);
  const [mappingType, setMappingType] = useState('vertex');

  const updateConfig = (updates: any) => {
    helpers.setValue({ ...field.value, ...updates });
  };

  return (
    <div className="yueshu-stream-config">
      <h3>配置映射 - {streamName}</h3>
      
      {/* 图空间 */}
      <FormField
        label="图空间"
        value={field.value?.graph || ''}
        onChange={(v) => updateConfig({ graph: v })}
      />
      
      {/* 映射类型 */}
      <RadioGroup
        label="映射类型"
        value={mappingType}
        options={[
          { value: 'vertex', label: '点表' },
          { value: 'edge', label: '边表' }
        ]}
        onChange={(v) => {
          setMappingType(v);
          updateConfig({ mapping_type: v });
        }}
      />
      
      {/* 条件渲染 */}
      {mappingType === 'vertex' ? (
        <VertexConfigForm 
          value={field.value}
          streamFields={streamFields}
          onChange={updateConfig}
        />
      ) : (
        <EdgeConfigForm 
          value={field.value}
          streamFields={streamFields}
          onChange={updateConfig}
        />
      )}
    </div>
  );
};
```

#### Step 3: 注册组件

在 `airbyte-webapp/src/views/Connector/DestinationForm/DestinationForm.tsx` 中注册：

```typescript
import { YueshuStreamConfig } from 'components/connector/YueshuDestination';

// 在组件中添加条件渲染
{destinationType === 'yueshu-destination' && (
  <YueshuStreamConfig 
    streamName={stream.name}
    streamFields={stream.jsonSchema.properties}
  />
)}
```

#### Step 4: 编译并部署

```bash
cd airbyte-webapp
npm install
npm run build
```

---

## 方案三：使用 Airbyte Cloud API（推荐给 SaaS 用户）

如果使用 Airbyte Cloud，可以通过 API 程序化配置：

### Step 1: 创建配置生成工具

```python
# tools/generate_connection_config.py
import json
from typing import Dict, Any, List

class AirbyteConfigGenerator:
    def __init__(self):
        self.streams = []
    
    def add_vertex_stream(
        self,
        stream_name: str,
        graph: str,
        label: str,
        primary_key_mapping: Dict[str, str],
        properties: List[Dict[str, str]] = None,
        write_mode: str = "insert or ignore"
    ):
        """添加点表映射"""
        config = {
            "stream": {"name": stream_name},
            "config": {
                "graph": graph,
                "mapping": {
                    "type": "vertex",
                    "label": label,
                    "primary_key": primary_key_mapping,
                    "properties": properties or []
                },
                "write_mode": write_mode
            }
        }
        self.streams.append(config)
        return self
    
    def add_edge_stream(
        self,
        stream_name: str,
        graph: str,
        label: str,
        src_vertex: Dict[str, Any],
        dst_vertex: Dict[str, Any],
        multiedge_key: Dict[str, str] = None,
        properties: List[Dict[str, str]] = None,
        write_mode: str = "insert or update"
    ):
        """添加边表映射"""
        mapping = {
            "type": "edge",
            "label": label,
            "src_vertex": src_vertex,
            "dst_vertex": dst_vertex,
            "properties": properties or []
        }
        
        if multiedge_key:
            mapping["multiedge_key"] = multiedge_key
        
        config = {
            "stream": {"name": stream_name},
            "config": {
                "graph": graph,
                "mapping": mapping,
                "write_mode": write_mode
            }
        }
        self.streams.append(config)
        return self
    
    def generate_catalog(self) -> Dict[str, Any]:
        """生成 Airbyte catalog 配置"""
        return {"streams": self.streams}
    
    def save(self, filepath: str):
        """保存配置到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.generate_catalog(), f, indent=2, ensure_ascii=False)

# 使用示例
if __name__ == "__main__":
    generator = AirbyteConfigGenerator()
    
    # 添加演员点表
    generator.add_vertex_stream(
        stream_name="actors",
        graph="movie",
        label="Actor",
        primary_key_mapping={
            "source_field": "id",
            "dest_field": "id"
        },
        properties=[
            {"source_field": "name", "dest_field": "name"},
            {"source_field": "birth_date", "dest_field": "birthDate", "transform": "date"}
        ]
    )
    
    # 添加演出边表
    generator.add_edge_stream(
        stream_name="acts",
        graph="movie",
        label="Act",
        src_vertex={
            "label": "Actor",
            "primary_key": {"source_field": "actor_id", "dest_field": "id"}
        },
        dst_vertex={
            "label": "Movie",
            "primary_key": {"source_field": "movie_id", "dest_field": "id"}
        },
        multiedge_key={"source_field": "role_id"},
        properties=[
            {"source_field": "role_name", "dest_field": "roleName"}
        ]
    )
    
    generator.save("configs/generated_catalog.json")
    print("✅ 配置已生成！")
```

### Step 2: 使用 Airbyte API 创建连接

```python
import requests

def create_airbyte_connection(
    api_url: str,
    api_key: str,
    source_id: str,
    destination_id: str,
    catalog_path: str
):
    """通过 API 创建 Airbyte 连接"""
    
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    
    response = requests.post(
        f"{api_url}/api/v1/connections/create",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "sourceId": source_id,
            "destinationId": destination_id,
            "syncCatalog": catalog,
            "status": "active"
        }
    )
    
    return response.json()
```

---

## 推荐实施路线

### 阶段一：快速上线（1-2天）
1. 实现方案一的 Step 1-3：更新 spec 并创建扁平化 schema
2. 测试基本的 UI 表单渲染
3. 手动在 Airbyte UI 中配置并验证

### 阶段二：完善功能（3-5天）
1. 实现 GQL 自动生成逻辑（方案一 Step 5-6）
2. 添加配置验证和错误处理
3. 端到端测试

### 阶段三：优化体验（可选，1-2周）
1. 如果 UI 体验不够好，考虑方案二
2. 开发自定义 React 组件
3. 优化交互和视觉设计

---

## 测试验证

### 本地测试

```bash
# 1. 测试 spec 输出
yueshu-airbyte --connector-type destination --command spec

# 2. 测试配置验证
yueshu-airbyte --connector-type destination --command check \
  --config configs/destination.optimized.json

# 3. 测试数据写入
yueshu-airbyte --connector-type destination --command write \
  --config configs/destination.optimized.json \
  --catalog configs/destination.catalog.optimized.json
```

### Docker 测试

```bash
# 构建镜像
docker build -f Dockerfile.destination -t yueshu-dest:test .

# 测试 spec
docker run --rm yueshu-dest:test spec

# 测试写入
docker run --rm \
  -v $(pwd)/configs:/configs \
  yueshu-dest:test write \
  --config /configs/destination.optimized.json \
  --catalog /configs/destination.catalog.optimized.json
```

---

## 常见问题

### Q1: Airbyte UI 不显示我的自定义字段？

**A**: 确保：
1. JSON Schema 格式正确，使用 `order` 字段控制显示顺序
2. 字段名称使用 `snake_case`
3. 提供 `title` 和 `description`

### Q2: 如何调试 UI 配置？

**A**: 
1. 在 Airbyte UI 中使用 "Edit JSON" 查看实际配置
2. 查看浏览器控制台的错误信息
3. 检查 connector 日志

### Q3: 能否混用新旧配置方式？

**A**: 可以！我们的实现支持向后兼容：
- 新 stream 使用 mapping 配置
- 旧 stream 继续使用 query_template

---

## 总结

**推荐方案一**作为初期实施方案，因为：
- ✅ 无需修改 Airbyte 源码
- ✅ 快速上线
- ✅ 维护成本低
- ✅ 官方支持

如果后续需要更复杂的 UI 交互，可以逐步迁移到方案二。
