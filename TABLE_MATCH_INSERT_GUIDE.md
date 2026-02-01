# TABLE MATCH INSERT 语法详解

> 基于 Yueshu 图数据库 5.2.0 文档

## 概述

`TABLE MATCH INSERT` 是 Yueshu 图数据库用于批量插入数据的高效语句。Connector 使用这种语法来实现批量数据导入。

## 基本语法

### 普通 INSERT 语句

**单个顶点插入：**
```gql
INSERT (@TagName{property1: value1, property2: value2})
```

**单条边插入：**
```gql
MATCH (src@TagName1{key: key1}), (dst@TagName2{key: key2})
INSERT (src)-[@EdgeType{prop: val}]->(dst)
```

### TABLE MATCH INSERT 语句

**批量顶点插入：**
```gql
TABLE
INSERT (@TagName{property1: value1, property2: value2})
INSERT (@TagName{property1: value1b, property2: value2b})
...
```

**批量边插入：**
```gql
TABLE
MATCH (src@TagName1{key: key1}), (dst@TagName2{key: key2})
INSERT (src)-[@EdgeType{prop: val}]->(dst)
MATCH (src@TagName1{key: key1b}), (dst@TagName2{key: key2b})
INSERT (src)-[@EdgeType{prop: valb}]->(dst)
...
```

## 详细说明

### TABLE 关键字

`TABLE` 关键字标记批量操作的开始，后续所有的 INSERT 语句都属于这个批量操作。

**优点：**
- 提高批量导入性能
- 减少网络往返次数
- 原子性操作（要么全部成功，要么全部失败）

### 顶点插入

#### 基本格式

```gql
INSERT (@TagName{field1: value1, field2: value2, ...})
```

#### 数据类型格式化

| 类型 | 格式 | 示例 |
|------|------|------|
| 整数 | `数字` | `age: 25` |
| 浮点数 | `数字.数字` | `height: 1.85` |
| 字符串 | `"文本"` | `name: "Tom Hanks"` |
| 日期 | `date("YYYY-MM-DD")` | `birthDate: date("1956-07-09")` |
| 日期时间 | `datetime("YYYY-MM-DD HH:MM:SS")` | `created: datetime("2024-01-15 10:30:00")` |
| 时间戳 | `timestamp("unix_timestamp")` | `updated: timestamp("1705320600")` |
| 布尔值 | `true` 或 `false` | `active: true` |
| NULL 值 | `NULL` | `email: NULL` |

#### 示例

```gql
TABLE
INSERT (@Actor{id: 1001, name: "Tom Hanks", birthDate: date("1956-07-09"), height: 183, active: true})
INSERT (@Actor{id: 1002, name: "Meg Ryan", birthDate: date("1961-11-19"), height: 171, active: true})
INSERT (@Actor{id: 1003, name: "Unknown", birthDate: NULL, height: NULL, active: false})
```

### 边插入

#### 基本格式

```gql
MATCH (src@SrcTag{key: value}), (dst@DstTag{key: value})
INSERT (src)-[@EdgeType{field1: value1, field2: value2}]->(dst)
```

#### MATCH 子句

- `src` 和 `dst` 是变量名，用于引用起点和终点
- 必须指定点的标签（TAG）和至少一个属性来唯一标识
- 多个匹配条件用逗号分隔

**示例：**
```gql
// 单个条件
MATCH (src@Actor{id: 1001})

// 多个条件
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})

// 多个属性
MATCH (src@Actor{id: 1001, name: "Tom"}), (dst@Movie{id: 2001})
```

#### 边的格式

**不含多边键（单边）：**
```gql
(src)-[@EdgeType{prop: val}]->(dst)
```

**含多边键（多边）：**
```gql
(src)-[@EdgeType:ranking_value{prop: val}]->(dst)
```

**无属性的边：**
```gql
(src)-[@EdgeType]->(dst)
```

**多边键说明：**
- `:` 后跟排名值（ranking key）
- 排名值可以是整数或字符串
- 同一对节点可以有多条边，通过排名值区分

#### 示例

```gql
// 单边关系
TABLE
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn{characterName: "Forrest Gump"}]->(dst)

// 多边关系（带排名值）
TABLE
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn:1{characterName: "Forrest Gump"}]->(dst)
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2002})
INSERT (src)-[@ActedIn:1{characterName: "Sam Baldwin"}]->(dst)

// 多条边
TABLE
MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn:1{characterName: "Forrest Gump", screenTime: 120}]->(dst)
MATCH (src@Actor{id: 1002}), (dst@Movie{id: 2001})
INSERT (src)-[@ActedIn:2{characterName: "Jenny", screenTime: 85}]->(dst)
MATCH (src@Actor{id: 1002}), (dst@Movie{id: 2002})
INSERT (src)-[@ActedIn:1{characterName: "Annie Reed", screenTime: 100}]->(dst)
```

## 冲突处理

### INSERT 模式

| 模式 | 语法 | 行为 | 用途 |
|------|------|------|------|
| INSERT | `TABLE INSERT ...` | 冲突时失败，报错 | 严格检查，不允许重复 |
| INSERT OR REPLACE | `TABLE INSERT OR REPLACE ...` | 冲突时替换 | 全量覆盖 |
| INSERT OR IGNORE | `TABLE INSERT OR IGNORE ...` | 冲突时忽略 | 首次加载，防重复 |
| INSERT OR UPDATE | `TABLE INSERT OR UPDATE ...` | 冲突时更新属性 | 增量更新 |

### 冲突条件

#### 顶点冲突

对于相同 TAG 的两个顶点，如果它们的**主键**相同，则视为冲突。

```gql
// 冲突示例（相同 id）
INSERT (@Actor{id: 1001, name: "Tom Hanks"})
INSERT (@Actor{id: 1001, name: "Tom H."})  // 冲突！
```

#### 边冲突

对于相同类型的两条边，如果以下条件满足，则视为冲突：

1. **如果定义了多边键：** 起点 + 终点 + 多边键相同
   ```gql
   // 冲突示例
   MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
   INSERT (src)-[@ActedIn:1{...}]->(dst)
   
   MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
   INSERT (src)-[@ActedIn:1{...}]->(dst)  // 冲突！相同 src, dst, ranking
   ```

2. **如果未定义多边键：** 起点 + 终点相同
   ```gql
   // 冲突示例（无多边键）
   MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
   INSERT (src)-[@ActedIn{...}]->(dst)
   
   MATCH (src@Actor{id: 1001}), (dst@Movie{id: 2001})
   INSERT (src)-[@ActedIn{...}]->(dst)  // 冲突！相同 src, dst
   ```

### 冲突处理示例

```gql
// 模式 1：INSERT（冲突时失败）
TABLE INSERT
INSERT (@Actor{id: 1001, name: "Tom"})
INSERT (@Actor{id: 1001, name: "Tom H."})  // ❌ 报错！

// 模式 2：INSERT OR REPLACE（冲突时替换）
TABLE INSERT OR REPLACE
INSERT (@Actor{id: 1001, name: "Tom"})
INSERT (@Actor{id: 1001, name: "Tom H."})  // ✅ 用新值替换

// 模式 3：INSERT OR IGNORE（冲突时忽略）
TABLE INSERT OR IGNORE
INSERT (@Actor{id: 1001, name: "Tom"})
INSERT (@Actor{id: 1001, name: "Tom H."})  // ✅ 保留原值 "Tom"

// 模式 4：INSERT OR UPDATE（冲突时更新）
TABLE INSERT OR UPDATE
INSERT (@Actor{id: 1001, name: "Tom", height: 183})
INSERT (@Actor{id: 1001, name: "Tom H.", height: NULL})  // ✅ 更新 name，height 变 NULL
```

## Connector 实现

### 生成流程

Connector 会根据配置自动：

1. 读取源数据
2. 根据映射规则转换数据
3. 生成 TABLE MATCH INSERT 语句
4. 按批次发送到图数据库

### 代码示例

见 `gql_generator.py`：

```python
def generate_gql_from_mapping(config, record):
    """根据配置和数据记录生成 GQL"""
    # ... 解析配置
    
    if config['type'] == 'vertex':
        # 生成 INSERT (@TagName{...})
        return f"INSERT (@{label}{{{attrs}}})"
    
    elif config['type'] == 'edge':
        # 生成 MATCH ... INSERT ...
        return f"MATCH {match_clause} INSERT {insert_clause}"

def _apply_table_insert(query, write_mode):
    """将查询包装在 TABLE 块中，应用写入模式"""
    # 1. 规范化写入模式
    # 2. 替换 INSERT 为 INSERT OR <mode>
    # 3. 用 TABLE 包装
    return f"TABLE {normalized_query}"
```

## 最佳实践

### 1. 批处理大小

**建议：**
- 单个 TABLE 块建议 100-1000 条语句
- 过大会导致内存占用过高
- 过小会影响性能

```python
# 示例：分批处理
BATCH_SIZE = 500
for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i+BATCH_SIZE]
    # 为 batch 生成 TABLE 块
```

### 2. 错误处理

**建议：**
- 检查 MATCH 条件是否能找到源点或终点
- 验证冲突处理模式是否符合业务需求
- 记录失败的数据行

### 3. 性能优化

**建议：**
- 为 TAG 的主键属性创建索引
  ```gql
  CREATE INDEX idx_actor_id ON Actor(id);
  ```
- 使用 INSERT OR IGNORE 而不是 INSERT
- 并行处理多个数据源

### 4. 调试

**建议：**
- 先用单条语句测试，再批量导入
- 查看同步日志了解生成的 GQL 语句
- 在不同数据量上测试

## 常见错误及解决方案

### 错误 1："[nebula] TagNotFound"

**原因：** MATCH 中的 TAG 名称不存在

**解决：**
```gql
// ❌ 错误
MATCH (src@Ctor{id: 1})  // 拼写错误

// ✅ 正确
MATCH (src@Actor{id: 1})
```

### 错误 2："[nebula] SemanticError"

**原因：** MATCH 条件无法找到匹配的节点

**解决：**
1. 验证节点是否已插入
2. 检查匹配条件的属性值
3. 对于边，确保源和目标节点都存在

### 错误 3："[nebula] PropertyNotFound"

**原因：** 属性名与 Schema 不一致

**解决：**
```gql
// ❌ 错误（属性名大小写不一致）
INSERT (@Actor{id: 1, birthdate: date("1990-01-01")})

// ✅ 正确
INSERT (@Actor{id: 1, birthDate: date("1990-01-01")})
```

### 错误 4："Conflict: Insert Conflict"

**原因：** 数据冲突且选择了 INSERT 模式

**解决：**
- 改用 INSERT OR REPLACE 或 INSERT OR IGNORE
- 或先删除冲突的数据

---

## 参考资源

- [Yueshu 官方文档 - INSERT 语句](https://docs.nebula-graph.com.cn/5.2.0/gql-guide/dml/insert/)
- [Connector 配置指南](./CONNECTOR_CONFIGURATION.md)
- [使用指南](./USAGE_GUIDE.md)
