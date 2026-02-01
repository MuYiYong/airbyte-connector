# Yueshu Airbyte Connector 使用指南

## 目录

1. [快速开始](#快速开始)
2. [详细配置步骤](#详细配置步骤)
3. [配置最佳实践](#配置最佳实践)
4. [故障排除](#故障排除)
5. [常见问题](#常见问题)

## 快速开始

### 前置条件

1. 已安装 Airbyte 并启动运行
2. 已部署 Yueshu 图数据库（NebulaGraph 5.2.0）
3. 已创建目标图（Graph）及其 Schema

### 5分钟快速配置

1. **在 Airbyte UI 中创建新的 Destination**
   - 选择 "Create new connector"
   - 搜索并选择 "Yueshu Airbyte Connector"

2. **填写 Connection 参数**
   ```
   Hosts: 192.168.1.100:9669
   User: root
   Password: nebula
   ```

3. **填写 Destination 参数**
   ```
   Graph: movie
   Insert Mode: insert or replace
   ```

4. **配置 Stream 映射**
   - 添加数据源表（Stream）
   - 定义顶点或边的映射
   - 指定字段对应关系

5. **测试连接**
   - 点击 "Test connection"
   - 等待连接成功提示

6. **启动同步**
   - 点击 "Sync now"
   - 监控同步进度

## 详细配置步骤

### 步骤 1：准备 Yueshu 图数据库

#### 1.1 创建图及其 Schema

```gql
CREATE GRAPH movie {
  CREATE TAG Actor {
    id int PRIMARY KEY,
    name string,
    birthDate date,
    height int,
    nationality string
  }
  
  CREATE TAG Movie {
    id int PRIMARY KEY,
    title string,
    releaseDate date,
    runtime int,
    primaryGenre string
  }
  
  CREATE EDGE ActedIn {
    characterName string,
    screenTime int
  }
}

USE movie;
```

#### 1.2 验证 Schema

```gql
SHOW TAGS;
SHOW EDGES;
DESCRIBE TAG Actor;
DESCRIBE EDGE ActedIn;
```

### 步骤 2：在 Airbyte 中配置 Connection

#### 2.1 创建新的 Connection

1. 打开 Airbyte UI
2. 进入 "Destination" 页面
3. 点击 "Create new destination"
4. 搜索 "Yueshu" 或 "NebulaGraph"
5. 选择 "Yueshu Airbyte Connector"

#### 2.2 填写 Connection 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| Hosts | `["192.168.1.100:9669"]` | 单个或多个主机地址和端口 |
| User | `root` | 数据库用户 |
| Password | `nebula` | 用户密码（需标记为敏感） |

**支持的 Hosts 格式：**
```
单个主机：
  ["localhost:9669"]

多个主机：
  ["host1:9669", "host2:9669", "host3:9669"]

带 IP 的多主机：
  ["192.168.1.100:9669", "192.168.1.101:9669"]
```

#### 2.3 测试连接

1. 点击 "Test connection" 按钮
2. 系统会尝试连接到数据库
3. 连接成功后显示绿色提示

**如果测试失败：**
- 检查 Hosts 地址和端口是否正确
- 确保网络连接到数据库服务器
- 验证用户名和密码

### 步骤 3：配置 Destination 参数

#### 3.1 选择 Graph

在 "Destination Settings" 中：

```
Graph: movie
```

这是在 Yueshu 中创建的图空间名称。

#### 3.2 选择写入模式

```
Insert Mode: insert or replace
```

**四种写入模式：**

| 模式 | 说明 | 场景 |
|------|------|------|
| `insert` | 如果冲突则失败 | 严格一致性，不允许重复 |
| `insert or replace` | 覆盖冲突的数据 | 全量同步，每次覆盖 |
| `insert or ignore` | 保留原数据，忽略新数据 | 首次加载，之后不覆盖 |
| `insert or update` | 更新冲突数据的属性 | 增量更新，保留未变更的属性 |

### 步骤 4：配置数据映射（Catalog）

#### 4.1 添加 Stream（数据源）

1. 在 Airbyte UI 的 Connection 配置中
2. 点击 "Add stream"
3. 选择或搜索数据源表
4. 配置该表的映射规则

#### 4.2 配置顶点映射

**示例：Actor 表映射到 Actor 点**

```json
{
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
      },
      {
        "source_field": "nationality",
        "dest_field": "nationality"
      }
    ]
  }
}
```

**关键字段说明：**

- `type`: 固定为 `"vertex"`
- `label`: 图中的点类型名称，必须与 Schema 中的 TAG 名称相同
- `primary_key`: 点的唯一标识
  - `source_field`: 源表中的字段名
  - `dest_field`: 图中的属性名
- `properties`: 其他属性映射数组
  - `source_field`: 源表字段名
  - `dest_field`: 图属性名
  - `transform`: （可选）类型转换（date、datetime、timestamp）

#### 4.3 配置边映射

**示例：ActedIn 表映射到 ActedIn 边**

```json
{
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
        "source_field": "character_name",
        "dest_field": "characterName"
      },
      {
        "source_field": "screen_time",
        "dest_field": "screenTime"
      }
    ]
  }
}
```

**关键字段说明：**

- `type`: 固定为 `"edge"`
- `label`: 图中的边类型名称
- `src_vertex`: 边的起点配置
  - `label`: 起点点类型名称
  - `primary_key`: 起点的主键映射
- `dst_vertex`: 边的终点配置
  - `label`: 终点点类型名称
  - `primary_key`: 终点的主键映射
- `multiedge_key`: （可选）多边键
  - 如果定义，同一对节点可以有多条边
  - 如果不定义，同一对节点只能有一条边
- `properties`: 边的属性映射数组

### 步骤 5：启动数据同步

#### 5.1 配置同步设置

1. 选择同步模式：
   - Full refresh：全量同步
   - Incremental：增量同步（如果支持）

2. 选择同步频率：
   - 单次执行
   - 定期执行（每小时/每天/每周）

#### 5.2 启动同步

1. 点击 "Sync now" 或 "Start"
2. Airbyte 会：
   - 从源系统读取数据
   - 根据映射规则生成 GQL 语句
   - 将数据插入到图数据库

#### 5.3 监控同步进度

1. 在 Airbyte UI 中查看同步日志
2. 检查：
   - 同步数据条数
   - 失败记录数
   - 同步耗时

## 配置最佳实践

### 1. 主键设计

**原则：**
- 主键字段在源数据中必须唯一且非 NULL
- 主键类型应与图数据库 Schema 兼容

**示例：**
```json
{
  "primary_key": {
    "source_field": "user_id",
    "dest_field": "uid"
  }
}
```

### 2. 属性映射

**原则：**
- 确保源字段存在于所有数据记录中
- 目标属性名必须与 Schema 中的定义一致

**常见错误：**
```json
// ❌ 错误：dest_field 与 Schema 中的属性名不一致
{
  "source_field": "birth_date",
  "dest_field": "birthdate"  // Schema 中定义的是 birthDate
}

// ✅ 正确
{
  "source_field": "birth_date",
  "dest_field": "birthDate"
}
```

### 3. 类型转换

**支持的转换：**

| 源格式 | Transform | 目标格式 |
|--------|-----------|---------|
| 字符串 | `date` | GQL date 类型 |
| 字符串 | `datetime` | GQL datetime 类型 |
| 字符串 | `timestamp` | GQL timestamp 类型 |
| - | 无 | 自动推断 |

**示例：**
```json
{
  "source_field": "created_at",
  "dest_field": "createdDate",
  "transform": "date"  // "2024-01-15" → date("2024-01-15")
}
```

### 4. 边的多边键

**何时使用：**
- 两个节点之间可能有多条边
- 使用额外字段来区分不同的边

**示例：**
```json
{
  "type": "edge",
  "label": "ActedIn",
  "multiedge_key": {
    "source_field": "role_id"  // 同一演员在同一电影中的不同角色
  }
}
```

**生成的 GQL：**
```gql
MATCH (src@Actor{id: 1}), (dst@Movie{id: 2})
INSERT (src)-[@ActedIn:100{...}]->(dst)  // :100 是多边键值
```

### 5. 写入模式选择

**选择建议：**

```
场景1：首次全量加载
  → 选择 "insert or ignore"
  → 防止重复数据

场景2：定期全量覆盖
  → 选择 "insert or replace"  
  → 每次完全替换数据

场景3：增量更新
  → 选择 "insert or update"
  → 只更新变化的属性

场景4：数据不可重复
  → 选择 "insert"
  → 冲突时报错
```

## 故障排除

### 连接问题

#### 问题：连接测试失败

**错误信息：**
```
Failed to connect to Yueshu at hosts: ...
```

**排查步骤：**

1. 验证网络连接
   ```bash
   ping 192.168.1.100
   telnet 192.168.1.100 9669
   ```

2. 检查 Yueshu 服务状态
   ```bash
   # 在数据库服务器上
   systemctl status nebula-graphd
   ```

3. 验证认证信息
   ```gql
   # 使用命令行客户端测试
   nebula-console -addr 192.168.1.100 -port 9669 -u root -p nebula
   SHOW GRAPHS;
   ```

### 数据插入问题

#### 问题：报错 "Graph not found"

**可能原因：**
- 指定的 Graph 不存在
- 用户没有访问权限

**解决方案：**
```gql
# 检查图是否存在
SHOW GRAPHS;

# 如果不存在，创建图
CREATE GRAPH movie { ... };
```

#### 问题：报错 "Tag not found"

**可能原因：**
- 配置中的 `label` 与 Schema 中的标签名不一致
- Schema 中尚未定义该标签

**解决方案：**
```gql
# 检查标签
SHOW TAGS;

# 创建缺失的标签
USE movie;
CREATE TAG Actor { ... };
```

#### 问题：报错 "Property not found"

**可能原因：**
- 配置中的属性名与 Schema 定义不一致
- 属性类型不匹配

**解决方案：**
```gql
# 检查标签的属性
DESCRIBE TAG Actor;

# 如果需要，修改 Schema
ALTER TAG Actor ADD (nationality string);
```

#### 问题：数据插入成功但字段值为 NULL

**可能原因：**
- 源数据中的字段值为 NULL
- `source_field` 映射错误

**解决方案：**
1. 检查源数据中是否有该字段
2. 验证 `source_field` 名称拼写
3. 查看 Airbyte 同步日志

### 性能问题

#### 问题：同步很慢

**优化建议：**

1. 增加批处理大小
   - 在 Destination 配置中调整批大小

2. 并行处理
   - 使用多个 Stream 配置并行同步

3. 索引优化
   - 在图数据库中创建必要的索引
   ```gql
   CREATE INDEX idx_actor_id ON Actor(id);
   ```

## 常见问题

### Q1：能否同时修改多个 Stream？

**A:** 可以。在 Airbyte Connection 配置中：
1. 添加多个 Stream
2. 每个 Stream 可以有独立的映射配置
3. 同步时会依次处理所有 Stream

### Q2：如何处理 NULL 值？

**A:** NULL 值会自动转换为 GQL 中的 NULL：
```json
{
  "source_field": "email",
  "dest_field": "email"
}
// 如果 email 为 NULL，生成：
// email: NULL
```

如果要跳过 NULL 值，需要在源端进行数据清理。

### Q3：支持嵌套属性吗？

**A:** 目前不支持嵌套对象。只支持标量属性（string、int、float、bool、date 等）。

### Q4：如何处理超大数据集？

**A:** 建议：
1. 分批导入
2. 使用增量同步
3. 优化 Source 查询性能
4. 在图数据库中创建索引

### Q5：支持回滚吗？

**A:** Airbyte Connector 本身不支持回滚。如需回滚：
1. 手动删除插入的数据
2. 恢复数据库备份

建议保留每次同步的备份。

### Q6：如何修改已配置的映射？

**A:** 
1. 在 Airbyte UI 中编辑 Connection 配置
2. 修改 Stream 的 `config` 部分
3. 保存并重新同步

**注意：** 修改后的映射只对新数据有效，已有数据需要手动处理。

---

**获取更多帮助：**
- 查看 [CONNECTOR_CONFIGURATION.md](../CONNECTOR_CONFIGURATION.md)
- 查看示例配置：[examples/movie_catalog.json](../examples/movie_catalog.json)
- 联系技术支持
