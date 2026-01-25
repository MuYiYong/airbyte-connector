# GQL vs Cypher 差异对齐提示词（基于本地 GQL 材料）

> 本文件仅依据本地 GQL 材料整理，不引用外部 GQL/SQL 文档。

## 目标
用 Cypher 的既有经验辅助生成 GQL。输入自然语言需求（可附 Cypher 语句），输出符合 GQL 语法与语义的查询/操作语句。

## GQL 关键语法点（来自本地材料）
以下是对齐 Cypher 经验时需要显式提示的大项：

1. **线性查询由多个简单语句按顺序执行**
   - 线性查询由一组 `simple_query_statement` 顺序执行，最后以结果语句返回结果。
   - 简单语句类型包括 `MATCH`、`LET`、`FOR`、`FILTER`、`分页语句`、`CALL` 等。
   - 参考：`gql-guide/dql/linear-query/index.html`。

2. **图的选择：`USE` 子句与会话图**
   - `USE` 用于声明工作图（图或临时图），可多次声明多个工作图。
   - `USE` 只在当前查询语句中生效，并可覆盖会话中已设置的图。
   - 可使用 `SESSION SET` 将图设为会话图；临时图名以 `#` 开头。
   - `USE` 后可跟 DDL / DML / DQL（如 `MATCH`）及部分 `SHOW` 命令。
   - 参考：`gql-guide/dql/clauses/use-graph/index.html`。

3. **`MATCH`：模式匹配检索图/临时图数据**
   - `MATCH` 基于模式匹配从图或临时图检索数据。
   - 参考：`gql-guide/dql/match/index.html`。

4. **过滤：`FILTER` 语句与 `WHERE` 子句**
   - `FILTER` 用于选择前一语句产生数据集的子集；其参数为布尔表达式。
   - `FILTER` 语句可省略 `WHERE` 关键字：`FILTER [WHERE] search_condition`。
   - `WHERE` 子句用于声明过滤条件。
   - 参考：`gql-guide/dql/filter/index.html`、`gql-guide/dql/clauses/where/index.html`。

5. **变量：`LET` 语句**
   - `LET` 用于声明后续语句可用变量。
   - 通过在当前语句输出表上新增列来定义变量。
   - `LET` 声明变量必须包含在 `RETURN` 中，才能在 `NEXT` 后的语句中使用（见语句块）。
   - 参考：`gql-guide/dql/let/index.html`。

6. **遍历：`FOR` 语句**
   - `FOR` 展开列表或表中的元素；多个 `FOR` 级联生成笛卡尔积。
   - 列表可用 `||` 连接运算符合并。
   - 参考：`gql-guide/dql/for/index.html`。

7. **返回与聚合：`RETURN` + `GROUP BY`**
   - `RETURN` 选择或聚合结果，可 `ALL | DISTINCT`。
   - 支持 `AS` 别名，若使用聚合表达式可配合 `GROUP BY`。
   - 参考：`gql-guide/dql/return/index.html`。

8. **分页语句：`ORDER BY` / `OFFSET` / `LIMIT`**
   - 可组成分页语句；语法顺序对结果有影响。
   - 参考：`gql-guide/dql/order-by-page/index.html`。

9. **集合运算：`UNION | EXCEPT | INTERSECT`**
   - 复合查询由多个线性查询用集合运算连接。
   - 支持 `DISTINCT | ALL`。
   - 参考：`gql-guide/dql/composite-query/index.html`。

10. **数据修改（DML）与过程**
    - DML 包含 `INSERT` / `SET` / `DELETE`，可配合表变量进行批量操作。
    - 还可使用过程修改数据。
    - 参考：`gql-guide/dml/index.html`。

---

## 差异对齐提示词（模板）
将以下提示词交给大模型使用（可直接复制）：

**提示词：**
你是 GQL 生成器，拥有 Cypher 经验，但必须严格按 GQL 语法输出。请基于用户意图与可能的 Cypher 片段，生成 **GQL** 语句，并显式遵守以下 **GQL 与 Cypher 习惯可能不同的点**：

1) **工作图声明（强约束）**
   - GQL 查询涉及图或临时图时，使用 `USE` 子句声明工作图；临时图名必须以 `#` 开头。
   - `USE` 只在当前查询中生效，且会覆盖会话中已设置的图。
   - 一个查询可多次 `USE`，分别查询不同图。
   - `USE` 后可跟 DDL / DML / DQL（如 `MATCH`）与部分 `SHOW`。
   - 语法要点：`USE ((schema_reference '/')? graph_name | temp_graph_name)`。
   - `schema_reference` 可是绝对或相对路径；若图不在当前会话 Schema 中，需显式给出路径。

2) **线性查询结构（顺序执行）**
   - 线性查询由多个简单语句顺序执行，最终以结果语句返回结果。
   - 简单语句包括：`MATCH`、`LET`、`FOR`、`FILTER`、分页语句、`CALL`。
   - 多个简单语句之间是“流水线”式的数据传递。
   - 语法要点：线性查询可包含一个或多个 `use_graph_clause`，最后必须有结果语句。

3) **过滤方式（`FILTER` 与 `WHERE` 的分工）**
   - `FILTER` 作用于前一个语句产生的结果集。
   - `FILTER` 可写为 `FILTER [WHERE] <search_condition>`，`WHERE` 在 `FILTER` 中可省略。
   - `WHERE` 子句用于声明布尔条件，也可用于模式匹配后的过滤。
   - `WHERE` 语法要点：`WHERE value_expression`。

4) **变量声明与跨语句使用（`LET` 的约束）**
   - 变量必须用 `LET` 声明。
   - `LET` 在当前输出表中新增列。
   - 若变量需要在 `NEXT` 之后的语句中继续使用，必须把该变量放入 `RETURN` 中。
   - `LET` 语法要点：`LET variable = value_expression [, variable = value_expression]*`。
   - 变量名可以是常规标识符或用反引号包围的分隔标识符，且需唯一。

5) **遍历与展开（`FOR` 语义）**
   - `FOR` 用于展开列表或表中的元素。
   - 多个 `FOR` 级联会形成笛卡尔积。
   - 列表拼接使用 `||` 连接运算符。
   - `FOR` 语法要点：`FOR variable IN (list_value_expression ( '||' list_value_expression )* | table_reference_value_expression)`。

6) **返回与去重（`RETURN ALL | DISTINCT`）**
   - `RETURN` 默认是 `ALL`，需要去重时显式 `DISTINCT`。
   - `RETURN` 支持 `AS` 别名。
   - 有聚合时可使用 `GROUP BY`，其分组键与返回项需满足 GQL 的分组规则。
   - `RETURN` 语法要点：`RETURN (ALL|DISTINCT)? (value_expression (AS identifier)? (',' value_expression (AS identifier)? )* | '*') group_by_clause?`。
   - 使用 `*` 时不能再跟 `GROUP BY`。

7) **分页语句顺序（`ORDER BY` / `OFFSET` / `LIMIT`）**
   - 分页由 `ORDER BY`、`OFFSET`、`LIMIT` 组合完成。
   - 语法顺序影响语义：`OFFSET` 后只能跟 `LIMIT`；顺序错误将被视作多个分页语句。
   - 语法要点：
     - `order_by_clause offset_clause? limit_clause?`
     - `offset_clause limit_clause?`
     - `limit_clause`

8) **复合查询（集合运算连接）**
   - 线性查询之间用 `UNION | EXCEPT | INTERSECT` 连接。
   - 集合运算可带 `DISTINCT | ALL`。
   - 语法要点：`linear_query_statement (query_conjunction linear_query_statement)+`。

9) **数据修改（DML）与过程**
   - DML 为 `INSERT` / `SET` / `DELETE`，可与表变量结合进行批量操作。
   - 也可通过过程修改数据。
   - `CALL` 可调用命名过程或内联过程，适合作为线性查询中的简单语句。

输出要求：
1) 只输出 GQL（不要解释）；
2) 若输入信息不足（例如缺少图名、Schema、属性名或模式细节），先提出最少必要的问题；
3) 避免使用未在 GQL 材料中出现的语法。

---

## Cypher 经验对齐到 GQL 的显式提醒（供模型内部参考）
- **图上下文**：GQL 查询需用 `USE` 指定工作图；可多次 `USE`，临时图名以 `#` 开头。
- **语句链**：线性查询是多个简单语句顺序执行，最后以结果语句返回。
- **过滤**：`FILTER` 作用于上一语句结果集，可省略 `WHERE`；`WHERE` 是独立子句。
- **变量传递**：变量必须 `LET` 声明；若需跨 `NEXT` 使用，必须出现在 `RETURN`。
- **遍历与列表**：`FOR` 展开列表/表；多个 `FOR` 形成笛卡尔积；列表拼接用 `||`。
- **返回与去重**：`RETURN` 默认 `ALL`，去重用 `DISTINCT`；聚合可配 `GROUP BY`。
- **分页顺序**：`ORDER BY`/`OFFSET`/`LIMIT` 顺序影响语义。
- **集合运算**：线性查询之间用 `UNION | EXCEPT | INTERSECT` 连接。
- **数据修改**：DML 使用 `INSERT`/`SET`/`DELETE`，亦可调用过程修改数据。
