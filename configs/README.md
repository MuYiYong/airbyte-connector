# 配置文件说明

本目录包含多种配置文件示例，展示不同的配置格式：

## Destination 配置文件

### 推荐格式（Mapping-based）

#### destination.catalog.sample.json
标准的层级 mapping 配置（**推荐使用**）
- 点表映射：选择源字段作为主键和属性
- 边表映射：配置起点、终点、多边键和属性
- 自动生成 GQL，无需手动编写查询语句

#### destination.catalog.optimized.json
与 sample 相同格式，包含更多示例

#### destination.catalog.flat.json
扁平化 mapping 配置
- 使用单层配置结构
- 自动转换为标准 mapping 格式
- 适合简单场景或程序化配置

### 传统格式（Legacy）

#### destination.optimized.json
手动编写 GQL 模板的传统方式
- 使用 `write_query_template` 字段
- 需要手动编写完整的 GQL 语句
- 仅供向后兼容，不推荐新项目使用

## Source 配置文件

#### source.sample.json
Source 连接配置

#### source.catalog.sample.json  
Source 数据读取配置

---

**建议**：新项目请使用 `destination.catalog.sample.json` 中的 mapping 格式配置。
