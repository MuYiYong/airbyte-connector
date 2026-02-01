# Yueshu Airbyte Connector 配置指南

## 概述

Yueshu Airbyte Connector（悦数图数据库 Airbyte 连接器）是一个专为 Yueshu 图数据库（NebulaGraph 5.2.0）设计的数据同步工具。

### 核心特性

- **连接配置与数据映射分离**：连接参数在 Connection 层配置，数据映射在 Destination 层配置
- **灵活的数据映射**：支持顶点和边的自定义属性映射
- **多种写入模式**：INSERT、INSERT OR REPLACE、INSERT OR IGNORE、INSERT OR UPDATE
- **批量插入**：使用 TABLE MATCH INSERT 语法进行高效的批量数据插入
- **Schema 感知**：自动读取图数据库的 Schema，支持类型感知的属性格式化

## Connection Configuration（连接配置）

Connection 层定义了如何连接到 Yueshu 图数据库。

### 连接参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `hosts` | string[] | 是 | - | 图数据库服务地址，格式：`["host1:port1", "host2:port2", ...]` |
| `user` | string | 否 | "root" | 连接用户名 |
| `password` | string | 否 | "root" | 连接密码（标记为敏感信息） |

### 示例连接配置（Connection Config）

```json
{
  "hosts": ["192.168.1.100:9669", "192.168.1.101:9669"],
  "user": "root",
  "password": "nebula"
}
```

## Destination Configuration（目标配置）

Destination 层定义了如何在连接基础上进行数据操作。

### 基础参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `graph` | string | 是 | - | 图空间名称 |
| `insert_mode` | enum | 否 | "insert or ignore" | 冲突处理模式：`insert`, `insert or replace`, `insert or ignore`, `insert or update` |

### 示例目标配置

```json
{
  "graph": "movie",
  "insert_mode": "insert or replace"
}
```

## Catalog 配置（数据映射）

Catalog 定义了 Airbyte 的数据流及其映射规则。对于图数据库，需要在每个 Stream 的配置中定义顶点和边的映射。

### Stream 配置格式

每个 Stream 代表一个数据源表。需要在该 Stream 的配置中定义：
1. 是否为顶点还是边
2. 属性到图元素的字段映射

### 顶点映射配置

```json
{
  "stream": "actor",
  "selected": true,
  "config": {
    "type": "vertex",
    "label": "Actor",
    "primary_key": {
      "source_field": "actor_id",
      "dest_field": "id"
    },
    "properties": [
      {
        "source_field": "actor_name",
        "dest_field": "name"
      },
      {
        "source_field": "birth_date",
        "dest_field": "birthDate",
        "transform": "date"
      },
      {
        "source_field": "height",
        "dest_field": "height"
      }
    ]
  }
}
```

**顶点配置说明：**

- `type`: 必须为 `vertex`
- `label`: 图中点的类型名称（对应 TAG）
- `primary_key`: 点的主键映射
  - `source_field`: 源数据字段名
  - `dest_field`: 目标图元素属性名
- `properties`: 其他属性的映射数组
  - `source_field`: 源数据字段名
  - `dest_field`: 目标图元素属性名  
  - `transform`: （可选）类型转换，支持 `date`, `datetime`, `timestamp`

### 边映射配置

```json
{
  "stream": "acted_in",
  "selected": true,
  "config": {
    "type": "edge",
    "label": "ActedIn",
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
        "source_field": "duration",
        "dest_field": "duration"
      }
    ]
  }
}
```

**边配置说明：**

- `type`: 必须为 `edge`
- `label`: 图中边的类型名称
- `src_vertex`: 边的起点配置
  - `label`: 起点顶点类型名称
  - `primary_key`: 起点的主键字段映射
- `dst_vertex`: 边的终点配置
  - `label`: 终点顶点类型名称
  - `primary_key`: 终点的主键字段映射
- `multiedge_key`: （可选）多边键配置，用于区分不同的边
  - `source_field`: 源数据中的多边键字段
- `properties`: 边的属性映射数组
  - `source_field`: 源数据字段名
  - `dest_field`: 目标边属性名
  - `transform`: （可选）类型转换

## 数据类型转换

Connector 支持以下数据类型转换：

### 日期时间类型

| Transform | 说明 | 示例 |
|-----------|------|------|
| `date` | 将字符串转换为日期 | `"2023-01-15"` → `date("2023-01-15")` |
| `datetime` | 将字符串转换为日期时间 | `"2023-01-15 10:30:00"` → `datetime("2023-01-15 10:30:00")` |
| `timestamp` | 将字符串转换为时间戳 | `"1673779200"` → `timestamp("1673779200")` |

### 数值类型

根据 Schema 中定义的数据类型自动转换：
- `int`, `int8`, `int16`, `int32`, `int64` → 整数
- `float`, `double` → 浮点数
- `bool`, `boolean` → 布尔值（true/false）

### 字符串类型

字符串值自动转义双引号，例如：
- `Hello "World"` → `"Hello \"World\""`

## 生成的 GQL 语句示例

### 点插入示例

对于上面的 Actor 配置，一条数据记录会生成：

```gql
INSERT (@Actor{id: 1001, name: "Tom Hanks", birthDate: date("1956-07-09"), height: 183})
```

### 边插入示例

对于上面的 ActedIn 配置，一条数据记录会生成：

```gql
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn:100{roleName: "Forrest Gump", duration: 175}]->(dst)
```

如果没有多边键，生成的语句：

```gql
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn{roleName: "Forrest Gump"}]->(dst)
```

### 批量插入（TABLE 模式）

Connector 会自动将 GQL 语句包装在 TABLE 块中进行批量处理：

```gql
TABLE
INSERT (@Actor{id: 1001, name: "Tom Hanks", birthDate: date("1956-07-09"), height: 183})
INSERT (@Actor{id: 1002, name: "Meg Ryan", birthDate: date("1961-11-19"), height: 171})
...
```

## 完整示例：Movie 数据库

### 1. 图 Schema 定义

```gql
CREATE GRAPH movie {
  CREATE TAG Person {
    id int PRIMARY KEY,
    name string,
    birthDate date
  }
  
  CREATE TAG Actor inherits Person {
    height int
  }
  
  CREATE TAG Director inherits Person {
    oscars int
  }
  
  CREATE TAG Movie {
    id int PRIMARY KEY,
    title string,
    releaseDate date,
    runtime int
  }
  
  CREATE TAG Genre {
    id int PRIMARY KEY,
    name string
  }
  
  CREATE EDGE ActedIn {
    role string,
    duration int
  }
  
  CREATE EDGE Directed {
    nominations int
  }
  
  CREATE EDGE WithGenre {
    position int
  }
}
```

### 2. Airbyte 配置

**Connection 配置：**
```json
{
  "hosts": ["localhost:9669"],
  "user": "root",
  "password": "nebula"
}
```

**Destination 配置：**
```json
{
  "graph": "movie",
  "insert_mode": "insert or replace"
}
```

**Catalog（actor_data stream）：**
```json
{
  "streams": [
    {
      "stream": "actor_data",
      "namespace": "source_db",
      "json_schema": { ... },
      "key_properties": ["actor_id"],
      "bookmark_properties": ["updated_at"],
      "is_resumable": false,
      "default_cursor_field": ["updated_at"],
      "supported_sync_modes": ["full_refresh", "incremental"],
      "source_defined_primary_key": [["actor_id"]],
      "config": {
        "type": "vertex",
        "label": "Actor",
        "primary_key": {
          "source_field": "actor_id",
          "dest_field": "id"
        },
        "properties": [
          {
            "source_field": "actor_name",
            "dest_field": "name"
          },
          {
            "source_field": "birth_date",
            "dest_field": "birthDate",
            "transform": "date"
          },
          {
            "source_field": "height",
            "dest_field": "height"
          }
        ]
      }
    }
  ]
}
```

## 注意事项

1. **主键验证**：确保映射中的主键字段在源数据中存在且唯一
2. **类型匹配**：源数据的数据类型应与目标图数据库的 Schema 兼容
3. **外键关系**：对于边的起点和终点，确保对应的顶点已经存在
4. **多边键**：如果边有多边键，不同的记录应该有不同的多边键值
5. **空值处理**：NULL 值会被正确转换为 GQL 中的 NULL

## 故障排除

### 连接失败

1. 检查 `hosts` 配置是否正确
2. 确保网络连接到数据库服务器
3. 验证用户名和密码

### 数据插入失败

1. 检查 Graph 名称是否存在
2. 验证 Label/TAG 名称是否与 Schema 匹配
3. 检查属性名称是否正确
4. 对于边，确保起点和终点顶点已存在

### 类型转换错误

1. 检查 `transform` 字段的值是否正确
2. 验证源数据的格式是否与转换类型兼容（如日期格式）

## Python 客户端版本

本 Connector 使用 **nebula5-python** 客户端库，对应 NebulaGraph 5.x 版本。

不支持 nebula3-python 或其他版本的客户端库。
