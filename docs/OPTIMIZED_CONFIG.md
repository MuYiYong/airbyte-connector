# 优化后的 Airbyte Connector 配置方案

## 概述

本优化方案简化了配置结构，采用声明式字段映射替代手写 GQL 模板，使用户更容易配置数据同步。

---

## 一、Connector 配置（连接信息）

### 配置结构

```json
{
  "host": "host:port",
  "user": "root",
  "password": "root"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `host` | string | 是 | - | 图数据库连接地址，格式为 `host:port` |
| `user` | string | 否 | `root` | 用户名 |
| `password` | string | 否 | `root` | 密码 |

### 配置示例

```json
{
  "host": "192.168.15.240:39669",
  "user": "root",
  "password": "root"
}
```

---

## 二、Connection 配置（字段映射）

Connection 配置采用声明式映射，connector 会自动生成相应的 GQL 语句。

### 2.1 点表映射 (Vertex Mapping)

#### 配置结构

```json
{
  "stream": {
    "name": "stream_name"
  },
  "config": {
    "graph": "graph_name",
    "mapping": {
      "type": "vertex",
      "label": "VertexLabel",
      "primary_key": {
        "source_field": "source_pk_field",
        "dest_field": "dest_pk_field"
      },
      "properties": [
        {
          "source_field": "source_field_name",
          "dest_field": "dest_field_name",
          "transform": "optional_transform_function"
        }
      ]
    },
    "write_mode": "insert or replace"
  }
}
```

#### 字段说明

| 字段路径 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| `stream.name` | string | 是 | 源端表名（Airbyte stream 名称） |
| `config.graph` | string | 是 | 目标图空间名称 |
| `config.mapping.type` | string | 是 | 映射类型，点表为 `"vertex"` |
| `config.mapping.label` | string | 是 | 目标点类型（Tag/Label） |
| `config.mapping.primary_key.source_field` | string | 是 | 源表中作为主键的字段名 |
| `config.mapping.primary_key.dest_field` | string | 是 | 目标点表中的主键字段名 |
| `config.mapping.properties` | array | 否 | 属性字段映射列表 |
| `config.mapping.properties[].source_field` | string | 是 | 源表字段名 |
| `config.mapping.properties[].dest_field` | string | 是 | 目标点表属性名 |
| `config.mapping.properties[].transform` | string | 否 | 转换函数（如 `date`、`datetime`） |
| `config.write_mode` | string | 否 | 写入模式，可选值见下文 |

#### 完整示例

```json
{
  "stream": {
    "name": "actors"
  },
  "config": {
    "graph": "movie",
    "mapping": {
      "type": "vertex",
      "label": "Actor",
      "primary_key": {
        "source_field": "id",
        "dest_field": "id"
      },
      "properties": [
        {
          "source_field": "name",
          "dest_field": "name"
        },
        {
          "source_field": "birth_date",
          "dest_field": "birthDate",
          "transform": "date"
        }
      ]
    },
    "write_mode": "insert or replace"
  }
}
```

#### 自动生成的 GQL 示例

对于上述配置，connector 会自动生成类似以下的 GQL 语句：

```gql
SESSION SET GRAPH movie;
TABLE INSERT (@Actor{
  id: {id},
  name: "{name}",
  birthDate: date("{birth_date}")
});
```

---

### 2.2 边表映射 (Edge Mapping)

#### 配置结构

```json
{
  "stream": {
    "name": "stream_name"
  },
  "config": {
    "graph": "graph_name",
    "mapping": {
      "type": "edge",
      "label": "EdgeLabel",
      "src_vertex": {
        "label": "SrcVertexLabel",
        "primary_key": {
          "source_field": "source_src_pk_field",
          "dest_field": "dest_src_pk_field"
        }
      },
      "dst_vertex": {
        "label": "DstVertexLabel",
        "primary_key": {
          "source_field": "source_dst_pk_field",
          "dest_field": "dest_dst_pk_field"
        }
      },
      "multiedge_key": {
        "source_field": "source_ranking_field"
      },
      "properties": [
        {
          "source_field": "source_field_name",
          "dest_field": "dest_field_name"
        }
      ]
    },
    "write_mode": "insert or update"
  }
}
```

#### 字段说明

| 字段路径 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| `stream.name` | string | 是 | 源端表名（Airbyte stream 名称） |
| `config.graph` | string | 是 | 目标图空间名称 |
| `config.mapping.type` | string | 是 | 映射类型，边表为 `"edge"` |
| `config.mapping.label` | string | 是 | 目标边类型（Edge Type） |
| `config.mapping.src_vertex.label` | string | 是 | 起点类型 |
| `config.mapping.src_vertex.primary_key.source_field` | string | 是 | 源表中起点主键字段名 |
| `config.mapping.src_vertex.primary_key.dest_field` | string | 是 | 目标图起点主键字段名 |
| `config.mapping.dst_vertex.label` | string | 是 | 终点类型 |
| `config.mapping.dst_vertex.primary_key.source_field` | string | 是 | 源表中终点主键字段名 |
| `config.mapping.dst_vertex.primary_key.dest_field` | string | 是 | 目标图终点主键字段名 |
| `config.mapping.multiedge_key.source_field` | string | 否 | 源表中作为 ranking/multiedge key 的字段 |
| `config.mapping.properties` | array | 否 | 属性字段映射列表 |
| `config.mapping.properties[].source_field` | string | 是 | 源表字段名 |
| `config.mapping.properties[].dest_field` | string | 是 | 目标边表属性名 |
| `config.write_mode` | string | 否 | 写入模式，可选值见下文 |

#### 完整示例

```json
{
  "stream": {
    "name": "acts"
  },
  "config": {
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
      "multiedge_key": {
        "source_field": "role_id"
      },
      "properties": [
        {
          "source_field": "role_name",
          "dest_field": "roleName"
        },
        {
          "source_field": "character_name",
          "dest_field": "characterName"
        }
      ]
    },
    "write_mode": "insert or update"
  }
}
```

#### 自动生成的 GQL 示例

对于上述配置，connector 会自动生成类似以下的 GQL 语句：

```gql
SESSION SET GRAPH movie;
TABLE MATCH (src@Actor{id: {actor_id}}), (dst@Movie{id: {movie_id}})
INSERT (src)-[@Act{
  roleName: "{role_name}",
  characterName: "{character_name}"
}]->(dst);
```

如果配置了 `multiedge_key`，会生成：

```gql
SESSION SET GRAPH movie;
TABLE MATCH (src@Actor{id: {actor_id}}), (dst@Movie{id: {movie_id}})
INSERT (src)-[@Act:{role_id}{
  roleName: "{role_name}",
  characterName: "{character_name}"
}]->(dst);
```

---

## 三、写入模式 (Write Mode)

| 模式 | 说明 |
|------|------|
| `insert` | 仅插入新记录，如果已存在则报错 |
| `insert or replace` | 插入或替换整条记录 |
| `insert or ignore` | 插入或忽略（默认） |
| `insert or update` | 插入或更新（合并属性） |

---

## 四、数据类型转换 (Transform)

在 `properties` 配置中可以指定 `transform` 字段进行类型转换：

| Transform 值 | 说明 | GQL 函数 |
|-------------|------|----------|
| `date` | 转换为日期类型 | `date("{field}")` |
| `datetime` | 转换为日期时间类型 | `datetime("{field}")` |
| `timestamp` | 转换为时间戳 | `timestamp("{field}")` |

未指定 `transform` 时，会根据字段类型自动处理：
- 字符串类型：使用双引号包裹
- 数值类型：直接使用
- 布尔类型：转换为 true/false

---

## 五、优化前后对比

### 优化前（手写 GQL 模板）

**Connector 配置：**
```json
{
  "hosts": [
    "192.168.15.240:39669",
    "192.168.15.241:39669"
  ],
  "username": "root",
  "password": "root"
}
```

**Catalog 配置：**
```json
{
  "stream": {"name": "acts"},
  "config": {
    "graph": "movie",
    "setup_queries": ["SESSION SET GRAPH movie"],
    "write_query_template": "TABLE t { actor_id, movie_id, movie_name } = ( {actor_id}, {movie_id}, \"{movie_name}\" )\nUSE movie\nFOR re IN t\nMATCH (a@Actor) WHERE a.id = re.actor_id\nINSERT (a)-[@Act]->(Movie {id: re.movie_id, name: re.movie_name})",
    "write_mode": "insert or update"
  }
}
```

❌ **问题：**
- 需要手写复杂的 GQL 模板
- 容易出错，难以维护
- 不直观，学习成本高

### 优化后（声明式映射）

**Connector 配置：**
```json
{
  "host": "192.168.15.240:39669",
  "user": "root",
  "password": "root"
}
```

**Catalog 配置：**
```json
{
  "stream": {"name": "acts"},
  "config": {
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
      "properties": [
        {
          "source_field": "role_name",
          "dest_field": "roleName"
        }
      ]
    },
    "write_mode": "insert or update"
  }
}
```

✅ **优势：**
- 声明式配置，清晰直观
- 自动生成 GQL 语句
- 易于理解和维护
- 降低配置错误风险

---

## 六、完整配置示例

### 6.1 Connector 配置文件

**文件：** `configs/destination.optimized.json`

```json
{
  "host": "192.168.15.240:39669",
  "user": "root",
  "password": "root"
}
```

### 6.2 Catalog 配置文件

**文件：** `configs/destination.catalog.optimized.json`

```json
{
  "streams": [
    {
      "stream": {
        "name": "actors"
      },
      "config": {
        "graph": "movie",
        "mapping": {
          "type": "vertex",
          "label": "Actor",
          "primary_key": {
            "source_field": "id",
            "dest_field": "id"
          },
          "properties": [
            {
              "source_field": "name",
              "dest_field": "name"
            },
            {
              "source_field": "birth_date",
              "dest_field": "birthDate",
              "transform": "date"
            }
          ]
        },
        "write_mode": "insert or replace"
      }
    },
    {
      "stream": {
        "name": "movies"
      },
      "config": {
        "graph": "movie",
        "mapping": {
          "type": "vertex",
          "label": "Movie",
          "primary_key": {
            "source_field": "movie_id",
            "dest_field": "id"
          },
          "properties": [
            {
              "source_field": "movie_name",
              "dest_field": "name"
            },
            {
              "source_field": "release_year",
              "dest_field": "releaseYear"
            }
          ]
        },
        "write_mode": "insert or replace"
      }
    },
    {
      "stream": {
        "name": "acts"
      },
      "config": {
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
          "multiedge_key": {
            "source_field": "role_id"
          },
          "properties": [
            {
              "source_field": "role_name",
              "dest_field": "roleName"
            },
            {
              "source_field": "character_name",
              "dest_field": "characterName"
            }
          ]
        },
        "write_mode": "insert or update"
      }
    }
  ]
}
```

---

## 七、实现要点

### 7.1 Connector 层面

1. **简化连接配置**
   - 将 `hosts` 数组改为单个 `host` 字符串
   - 将 `username` 改为 `user`
   - 保持默认值为 `root`

2. **移除冗余配置**
   - 移除 `setup_queries`（改为自动生成 `SESSION SET GRAPH` 语句）
   - 移除手写的 `write_query_template`

### 7.2 Mapping 解析

根据 `mapping.type` 判断是点表还是边表，然后：

**点表 (vertex)：**
```python
def generate_vertex_insert(mapping, record):
    graph = mapping['graph']
    label = mapping['label']
    pk = mapping['primary_key']
    properties = mapping.get('properties', [])
    
    # 构建属性列表
    attrs = [f"{pk['dest_field']}: {format_value(record[pk['source_field']])}"]
    
    for prop in properties:
        source_val = record[prop['source_field']]
        transform = prop.get('transform')
        formatted = apply_transform(source_val, transform)
        attrs.append(f"{prop['dest_field']}: {formatted}")
    
    attrs_str = ', '.join(attrs)
    return f"SESSION SET GRAPH {graph};\nTABLE INSERT (@{label}{{{attrs_str}}});"
```

**边表 (edge)：**
```python
def generate_edge_insert(mapping, record):
    graph = mapping['graph']
    label = mapping['label']
    src = mapping['src_vertex']
    dst = mapping['dst_vertex']
    multiedge = mapping.get('multiedge_key')
    properties = mapping.get('properties', [])
    
    # 构建 MATCH 子句
    src_pk_val = record[src['primary_key']['source_field']]
    dst_pk_val = record[dst['primary_key']['source_field']]
    
    match_clause = f"MATCH (src@{src['label']}{{{src['primary_key']['dest_field']}: {format_value(src_pk_val)}}}), "
    match_clause += f"(dst@{dst['label']}{{{dst['primary_key']['dest_field']}: {format_value(dst_pk_val)}}})"
    
    # 构建 ranking
    ranking = ""
    if multiedge:
        ranking_val = record[multiedge['source_field']]
        ranking = f":{ranking_val}"
    
    # 构建属性
    attrs = []
    for prop in properties:
        source_val = record[prop['source_field']]
        formatted = format_value(source_val)
        attrs.append(f"{prop['dest_field']}: {formatted}")
    
    attrs_str = ', '.join(attrs) if attrs else ''
    edge_clause = f"(src)-[@{label}{ranking}{{{attrs_str}}}]->(dst)"
    
    return f"SESSION SET GRAPH {graph};\nTABLE {match_clause}\nINSERT {edge_clause};"
```

### 7.3 类型转换

```python
def apply_transform(value, transform):
    if transform == 'date':
        return f'date("{value}")'
    elif transform == 'datetime':
        return f'datetime("{value}")'
    elif transform == 'timestamp':
        return f'timestamp("{value}")'
    else:
        return format_value(value)

def format_value(value):
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    else:
        return str(value)
```

---

## 八、总结

通过采用声明式配置，我们实现了：

1. ✅ **简化连接配置** - 只需 `host`、`user`、`password` 三个字段
2. ✅ **声明式映射** - 用户只需描述字段映射关系，无需手写 GQL
3. ✅ **自动生成 GQL** - Connector 根据映射自动生成正确的 GQL 语句
4. ✅ **类型安全** - 通过 `transform` 字段支持类型转换
5. ✅ **易于维护** - 配置结构清晰，便于理解和维护
6. ✅ **降低错误** - 避免手写 GQL 导致的语法错误

这种方式将复杂的 GQL 语法封装在 Connector 内部，让用户专注于业务层面的字段映射关系，大大降低了使用门槛。
