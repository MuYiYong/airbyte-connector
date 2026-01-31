# Airbyte UI 配置指南

本文档介绍如何在 Airbyte UI 中配置悦数图数据库连接器。

---

## 一、Connector 配置（连接信息）

在 Airbyte UI 中创建 Destination 时，会看到以下配置表单：

### 配置字段

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| **图数据库地址** | 数组 | ✅ | - | nebula 图数据库的连接地址列表 |
| **用户名** | 字符串 | ❌ | `root` | 数据库用户名 |
| **密码** | 字符串 | ❌ | `root` | 数据库密码（敏感信息，会被遮蔽） |

### UI 界面示例

```
┌─────────────────────────────────────────────┐
│ 图数据库地址 *                               │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ 192.168.15.240:39669                    │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ 192.168.15.241:39669                    │ │
│ └─────────────────────────────────────────┘ │
│ [+ 添加地址]                                │
├─────────────────────────────────────────────┤
│ 用户名                                      │
│ ┌─────────────────────────────────────────┐ │
│ │ root                                    │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ 密码                                        │
│ ┌─────────────────────────────────────────┐ │
│ │ ••••                                    │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 配置说明

1. **图数据库地址**：可以添加多个 `host:port` 地址，格式为 `ip:port` 或 `hostname:port`
   - 例如：`192.168.15.240:39669`
   - 点击"添加地址"按钮可以添加更多地址
   
2. **用户名**和**密码**：如不填写，默认使用 `root`/`root`

---

## 二、Connection 配置（字段映射）

创建连接后，在配置 Catalog 时需要为每个 stream 配置映射关系。

### 配置入口

在 Airbyte UI 的 **Configure Connection** 页面：
1. 选择需要同步的 streams
2. 点击右上角的 **"Edit JSON"** 按钮
3. 在 JSON 编辑器中为每个 stream 添加 `config` 配置

### 配置结构

每个 stream 的配置包含以下部分：

```json
{
  "streams": [
    {
      "stream": {"name": "stream_name"},
      "config": {
        "graph": "图空间名称",
        "mapping": { /* 映射配置 */ },
        "write_mode": "写入模式"
      }
    }
  ]
}
```

---

## 三、点表映射配置

### UI 配置示例

在 **Edit JSON** 中配置点表映射：

```json
{
  "stream": {"name": "actors"},
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

### 配置步骤

1. **设置映射类型**：`"type": "vertex"` 表示这是点表映射

2. **配置点类型标签**：`"label": "Actor"` 指定目标图中的点类型

3. **配置主键映射**：
   - `source_field`：源表中的主键字段名（如 `"id"`）
   - `dest_field`：目标图中的点主键字段名（如 `"id"`）

4. **配置属性映射**（可选）：
   - 为每个需要同步的字段添加一个映射项
   - `source_field`：源表字段名
   - `dest_field`：目标图属性名
   - `transform`：可选的类型转换（`date`、`datetime`、`timestamp`）

5. **选择写入模式**：
   - `insert`：仅插入
   - `insert or replace`：插入或替换
   - `insert or ignore`：插入或忽略（默认）
   - `insert or update`：插入或更新

---

## 四、边表映射配置

### UI 配置示例

在 **Edit JSON** 中配置边表映射：

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
      "multiedge_key": {
        "source_field": "role_id"
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

### 配置步骤

1. **设置映射类型**：`"type": "edge"` 表示这是边表映射

2. **配置边类型标签**：`"label": "Act"` 指定目标图中的边类型

3. **配置起点信息**（`src_vertex`）：
   - `label`：起点的类型标签（如 `"Actor"`）
   - `primary_key.source_field`：源表中起点主键字段名（如 `"actor_id"`）
   - `primary_key.dest_field`：目标图中起点主键字段名（如 `"id"`）

4. **配置终点信息**（`dst_vertex`）：
   - `label`：终点的类型标签（如 `"Movie"`）
   - `primary_key.source_field`：源表中终点主键字段名（如 `"movie_id"`）
   - `primary_key.dest_field`：目标图中终点主键字段名（如 `"id"`）

5. **配置多边键**（可选）：
   - 如果边支持多重边（同一起点和终点之间可以有多条边），需要配置 `multiedge_key`
   - `source_field`：源表中作为 ranking 的字段名

6. **配置边属性**（可选）：
   - 为边的每个属性字段添加映射
   - 配置方式与点表属性映射相同

7. **选择写入模式**

---

## 五、完整配置示例

### 场景：将电影数据库同步到图数据库

假设源数据库有三张表：
- `actors`：演员表（id, name, birth_date）
- `movies`：电影表（movie_id, movie_name, release_year）
- `acts`：演出关系表（actor_id, movie_id, role_id, role_name）

目标图空间 `movie` 有：
- 点类型 `Actor`（id, name, birthDate）
- 点类型 `Movie`（id, name, releaseYear）
- 边类型 `Act`（roleName）

### Airbyte Connection 配置

在 **Edit JSON** 中配置如下：

```json
{
  "streams": [
    {
      "stream": {"name": "actors"},
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
      "stream": {"name": "movies"},
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
          "multiedge_key": {
            "source_field": "role_id"
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
  ]
}
```

---

## 六、配置流程总结

### 6.1 创建 Destination

1. 在 Airbyte UI 中点击 **"New Destination"**
2. 选择 **"悦数图数据库 (yueshu-airbyte-destination)"**
3. 填写连接配置：
   - 添加一个或多个图数据库地址（host:port）
   - 填写用户名和密码（或使用默认值）
4. 点击 **"Test"** 验证连接
5. 点击 **"Save"** 保存

### 6.2 创建 Connection

1. 创建或选择一个 Source
2. 点击 **"New Connection"**，选择刚创建的 Destination
3. 在 **"Configure Connection"** 页面：
   - 选择需要同步的 streams
   - 点击右上角 **"Edit JSON"**
   - 为每个 stream 添加 `config` 配置（参考上述示例）
4. 点击 **"Save"** 保存配置
5. 运行同步任务

---

## 七、常见问题

### Q1: 如何添加多个数据库地址？

在 Connector 配置页面，点击"图数据库地址"下方的 **[+ 添加地址]** 按钮，可以添加多个 host:port。

### Q2: 为什么在 Airbyte UI 看不到字段映射配置？

Airbyte 默认不会为自定义的 stream config 生成 UI 表单。需要：
1. 在 **Configure Connection** 页面点击 **"Edit JSON"**
2. 手动编辑 JSON 配置添加 `config` 字段

### Q3: 如何知道源表有哪些字段？

在配置 Connection 时，Airbyte 会自动探测源表的 schema，你可以在 stream 详情中查看所有字段。

### Q4: multiedge_key 是什么？

multiedge_key（多边键）用于支持同一起点和终点之间的多条边。在 NebulaGraph 中也叫 ranking。如果不需要多重边，可以省略此配置。

### Q5: transform 支持哪些类型转换？

目前支持：
- `date`：转换为日期类型
- `datetime`：转换为日期时间类型
- `timestamp`：转换为时间戳类型
- 留空：使用原始类型

---

## 八、JSON Schema 说明

为了让 Airbyte 能够在 UI 中生成配置表单，connector 需要提供 JSON Schema 定义。

### Connector Spec Schema

位置：`specs/destination_spec.json`

定义了 Connector 级别的配置（hosts, user, password），Airbyte 会根据这个 schema 自动生成配置表单。

### Stream Config Schema

位置：`specs/stream_config_spec.json`

定义了 Stream 级别的配置（graph, mapping, write_mode），用于在 Airbyte UI 中通过 JSON 编辑器配置字段映射。

> **注意**：目前 Airbyte 对 per-stream 自定义配置的 UI 支持有限，通常需要使用 **Edit JSON** 功能手动配置。

---

## 九、最佳实践

1. **先配置点表，再配置边表**
   - 确保点数据先同步，再同步边数据
   - 在 Airbyte 中可以设置 stream 的依赖顺序

2. **使用有意义的字段名**
   - `dest_field` 命名要清晰，便于在图查询中使用
   - 遵循图数据库的命名规范（如驼峰命名）

3. **选择合适的写入模式**
   - 初次同步：使用 `insert` 或 `insert or replace`
   - 增量同步：使用 `insert or update` 或 `insert or ignore`

4. **验证配置正确性**
   - 配置完成后先运行小批量数据测试
   - 在图数据库中查询验证数据是否正确导入

5. **维护配置文档**
   - 记录每个表的映射关系
   - 便于后续维护和问题排查
