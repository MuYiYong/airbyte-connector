# Yueshu 5.2.0 TABLE INSERT 批量操作语法参考

根据官方文档，Yueshu 5.2.0 使用 **TABLE INSERT** 进行批量数据操作。

## 基本语法

### 1. 定义表变量 (TABLE Variable) 用于批量操作

```sql
TABLE t { field1, field2, field3 } = [ 
  { field1: value1, field2: value2, field3: value3 },
  { field1: value1, field2: value2, field3: value3 },
  ...
]
```

### 2. 使用表变量进行批量 INSERT 顶点

```sql
TABLE actors { id, name, birthDate } = [
  { id: 1, name: "Alice", birthDate: date("1990-01-01") },
  { id: 2, name: "Bob", birthDate: date("1991-02-01") }
]
INSERT (@Actor { id: actors.id, name: actors.name, birthDate: actors.birthDate })
```

### 3. 使用表变量进行批量 INSERT 边

```sql
TABLE t { actor_id, movie_id, movie_name } = [
  { actor_id: 1, movie_id: 101, movie_name: "Movie1" },
  { actor_id: 2, movie_id: 102, movie_name: "Movie2" }
]
INSERT (a:Actor{id: t.actor_id})-[@Act]->(m:Movie{id: t.movie_id, name: t.movie_name})
```

### 4. 直接批量插入多个顶点 (不使用表变量)

```sql
INSERT (@Actor{id:1, name:"Alice", birthDate:date("1990-01-01")}),
       (@Actor{id:2, name:"Bob", birthDate:date("1991-02-01")})
```

### 5. 批量插入多条边

```sql
INSERT (a:Actor{id:1})-[@Act]->(m:Movie{id:101}),
       (b:Actor{id:2})-[@Act]->(m:Movie{id:102})
```

## 冲突处理模式

TABLE INSERT 支持以下冲突处理方式：

```sql
INSERT (@Actor{id:1, name:"Alice"})
INSERT OR REPLACE (@Actor{id:1, name:"Alice"})
INSERT OR IGNORE (@Actor{id:1, name:"Alice"})
INSERT OR UPDATE (@Actor{id:1, name:"Alice"})
```

- `INSERT` - 默认插入，如果存在则报错
- `INSERT OR REPLACE` - 重复时替换整个顶点/边
- `INSERT OR IGNORE` - 重复时忽略，不报错
- `INSERT OR UPDATE` - 重复时更新属性值

## 数据类型和转换

```sql
-- 日期
date("YYYY-MM-DD")

-- 日期时间
datetime("YYYY-MM-DDTHH:MM:SS")

-- 时间戳
timestamp("YYYY-MM-DDTHH:MM:SS")

-- 字符串 (双引号)
name: "string value"

-- 数字
id: 123, price: 99.99

-- 布尔值
active: true, deleted: false

-- 列表 (用于多值字段)
tags: ["tag1", "tag2"]
```

## Python 中的使用示例

### 使用表变量进行批量操作

```python
from nebulagraph_python import NebulaClient

with NebulaClient(
    hosts=["192.168.15.240:39669"],
    username="root",
    password="Nebula123",
) as client:
    # 定义表变量并执行批量 INSERT
    query = """
        TABLE actors { actor_id, actor_name } = [
            { actor_id: 1, actor_name: "Alice" },
            { actor_id: 2, actor_name: "Bob" },
            { actor_id: 3, actor_name: "Charlie" }
        ]
        INSERT (@Actor { id: actors.actor_id, name: actors.actor_name })
    """
    result = client.execute(query)
    print(f"插入成功: {result}")
```

### 直接批量插入多行

```python
query = """
    INSERT (@Actor{id:1, name:"Alice"}),
           (@Actor{id:2, name:"Bob"}),
           (@Actor{id:3, name:"Charlie"})
"""
result = client.execute(query)
```

### 使用 INSERT OR IGNORE 处理重复

```python
query = """
    TABLE t { id, name } = [
        { id: 1, name: "Alice" },
        { id: 2, name: "Bob" }
    ]
    INSERT OR IGNORE (@Actor { id: t.id, name: t.name })
"""
result = client.execute(query)
```

## 性能优化建议

1. **使用 TABLE 变量** - 比多条 INSERT 语句更高效
2. **批量操作** - 在一条语句中插入多个元素
3. **选择合适的冲突处理模式**:
   - 完全新数据: 使用 `INSERT`
   - 允许重复忽略: 使用 `INSERT OR IGNORE`
   - 需要更新: 使用 `INSERT OR UPDATE`
   - 需要替换: 使用 `INSERT OR REPLACE`

## 注意事项

1. **不需要 OPEN GRAPH 或 USE** - 直接在 INSERT 语句中操作
2. **使用 @ 标记节点类型** - `@Actor`, `@Movie` 等（对应图的顶点标签）
3. **变量引用** - TABLE 变量中的字段通过 `t.field_name` 引用
4. **表变量作用域** - 仅在同一条语句中有效
5. **性能考虑** - 大批量操作建议使用 TABLE 变量

## 参考文档

- Yueshu 5.2.0 INSERT 官方文档: `/Users/muyi/Downloads/yueshu-graph-5.2.0/127.0.0.1_8000/gql-guide/dml/insert/`
- 表变量官方文档: `/Users/muyi/Downloads/yueshu-graph-5.2.0/127.0.0.1_8000/gql-guide/variable-definition/table-variable/`
- nebula5-python 文档: https://github.com/vesoft-inc/nebula-python/tree/v5.2.1/docs
