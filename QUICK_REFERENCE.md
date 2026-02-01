# Yueshu Connector 快速参考卡片

## Connection 配置（连接层）

```json
{
  "hosts": ["192.168.1.100:9669"],
  "user": "root",
  "password": "nebula"
}
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `hosts` | 数据库地址和端口 | `["localhost:9669"]` 或 `["host1:9669", "host2:9669"]` |
| `user` | 用户名（可选） | `root` |
| `password` | 密码（可选，敏感信息） | `nebula` |

---

## Destination 配置（目标层）

```json
{
  "graph": "movie",
  "insert_mode": "insert or replace"
}
```

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `graph` | 目标图空间 | 任意已创建的图名称 |
| `insert_mode` | 冲突处理模式 | `insert`, `insert or replace`, `insert or ignore`, `insert or update` |

---

## 冲突处理模式

| 模式 | 冲突行为 | 适用场景 |
|------|---------|---------|
| `insert` | 报错 | 严格检查，禁止重复 |
| `insert or replace` | 覆盖 | 全量覆盖 |
| `insert or ignore` | 忽略 | 首次加载（默认） |
| `insert or update` | 更新属性 | 增量更新 |

---

## Catalog 配置：顶点映射

```json
{
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
    }
  ]
}
```

**关键字段：**
- `type`: 固定为 `vertex`
- `label`: 点的类型名称（TAG）
- `primary_key`: 点的主键映射
- `properties`: 其他属性映射

---

## Catalog 配置：边映射

```json
{
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
      "source_field": "character_name",
      "dest_field": "characterName"
    }
  ]
}
```

**关键字段：**
- `type`: 固定为 `edge`
- `label`: 边的类型名称
- `src_vertex`: 起点配置
- `dst_vertex`: 终点配置
- `multiedge_key`: 多边键（可选）
- `properties`: 边的属性

---

## 数据类型转换

| 源数据 | Transform | GQL 格式 | 说明 |
|--------|-----------|---------|------|
| `"Tom"` | 无 | `"Tom"` | 字符串自动加引号和转义 |
| `123` | 无 | `123` | 整数直接转换 |
| `1.23` | 无 | `1.23` | 浮点数直接转换 |
| `"2024-01-15"` | `date` | `date("2024-01-15")` | 日期 |
| `"2024-01-15 10:30:00"` | `datetime` | `datetime("2024-01-15 10:30:00")` | 日期时间 |
| `"1705320600"` | `timestamp` | `timestamp("1705320600")` | 时间戳 |
| 布尔值 | 无 | `true` / `false` | 自动转换 |
| `NULL` | 无 | `NULL` | 空值 |

---

## 生成的 GQL 示例

### 单个顶点插入
```gql
INSERT (@Actor{id: 1001, name: "Tom Hanks", birthDate: date("1956-07-09")})
```

### 单条边插入（无多边键）
```gql
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn{characterName: "Forrest Gump"}]->(dst)
```

### 单条边插入（有多边键）
```gql
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn:1{characterName: "Forrest Gump"}]->(dst)
```

### 批量插入
```gql
TABLE
INSERT (@Actor{id: 1001, name: "Tom Hanks"})
INSERT (@Actor{id: 1002, name: "Meg Ryan"})
```

---

## 常见错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| 连接失败 | hosts/port 错误 | 验证数据库地址 |
| Graph not found | 图不存在 | 创建图：`CREATE GRAPH movie { ... }` |
| Tag not found | 点类型不存在 | 创建 TAG：`CREATE TAG Actor { ... }` |
| Property not found | 属性不存在或名称不一致 | 检查 Schema，确保属性名一致 |
| MATCH 无法找到源点 | 起点或终点不存在 | 确保先插入源点数据 |
| 数据插入值为 NULL | 字段映射错误或源数据为空 | 检查 source_field 名称和源数据 |

---

## 配置检查清单

- [ ] Connection 中的 `hosts` 地址和端口正确
- [ ] Destination 中的 `graph` 名称与数据库中存在的图一致
- [ ] Catalog 中每个 Stream 的 `type` 字段正确（vertex 或 edge）
- [ ] Catalog 中的 `label` 与 Schema 中的 TAG 或 EDGE 名称一致
- [ ] 顶点映射中指定了 `primary_key`
- [ ] 边映射中正确指定了 `src_vertex` 和 `dst_vertex`
- [ ] 属性名称（`dest_field`）与 Schema 中的定义一致
- [ ] 日期格式的转换使用了正确的 `transform` 值
- [ ] 所有必需的源字段（`source_field`）在数据源中都存在

---

## 快速开始（5分钟）

1. **创建 Connection** → 输入 hosts、user、password
2. **测试连接** → 点击 "Test connection"
3. **配置 Destination** → 选择 graph、insert_mode
4. **添加 Streams** → 为每个数据源表配置映射
5. **启动同步** → 点击 "Sync now"

---

## 需要帮助？

- **完整配置参考** → [CONNECTOR_CONFIGURATION.md](./CONNECTOR_CONFIGURATION.md)
- **详细使用指南** → [USAGE_GUIDE.md](./USAGE_GUIDE.md)
- **SQL 语法详解** → [TABLE_MATCH_INSERT_GUIDE.md](./TABLE_MATCH_INSERT_GUIDE.md)
- **代码示例** → [examples/configuration_examples.py](./examples/configuration_examples.py)
- **Catalog 示例** → [examples/movie_catalog.json](./examples/movie_catalog.json)

---

## 支持的数据库

- **Yueshu 图数据库** 5.2.0
- **客户端库**: nebula5-python

---

**版本**: 1.0  
**最后更新**: 2024 年 1 月 15 日
