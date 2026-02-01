# 文档索引和导航

欢迎使用 Yueshu Airbyte Connector！本页面帮助您快速找到所需的文档。

## 📚 文档列表

### 🚀 快速开始（推荐首先阅读）

| 文档 | 适用人群 | 阅读时间 |
|------|---------|---------|
| [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) | 所有用户 | 5 分钟 |
| [快速开始部分（USAGE_GUIDE.md）](./USAGE_GUIDE.md#快速开始) | 新用户 | 10 分钟 |

### 📖 详细指南

| 文档 | 内容 | 适用人群 |
|------|------|---------|
| [USAGE_GUIDE.md](./USAGE_GUIDE.md) | **详细的操作指南** | 所有用户 |
| | • 快速开始（5分钟） | |
| | • 详细配置步骤（逐步） | 新手用户 |
| | • 配置最佳实践 | 有经验的用户 |
| | • 故障排除和常见问题 | 所有用户 |
| [CONNECTOR_CONFIGURATION.md](./CONNECTOR_CONFIGURATION.md) | **完整的配置参考** | 开发者 |
| | • 连接参数说明 | |
| | • 顶点映射配置 | |
| | • 边映射配置 | |
| | • 数据类型转换 | |
| | • 完整示例 | |
| [TABLE_MATCH_INSERT_GUIDE.md](./TABLE_MATCH_INSERT_GUIDE.md) | **GQL 语法深入指南** | 高级用户 |
| | • 语法详解 | |
| | • 数据类型格式化规则 | |
| | • 冲突处理模式详解 | |
| | • 常见错误及解决方案 | |

### 💻 代码和示例

| 文件 | 说明 | 用途 |
|------|------|------|
| [examples/configuration_examples.py](./examples/configuration_examples.py) | Python 代码示例 | • 学习配置代码化表示 |
| | | • 复制和修改示例 |
| [examples/movie_catalog.json](./examples/movie_catalog.json) | 完整的 Airbyte Catalog | • 参考实际配置格式 |
| | | • 直接导入到 Airbyte |

### 📋 项目文档

| 文档 | 内容 |
|------|------|
| [README.md](./README.md) | 项目简介和集成指南 |
| [RECONFIGURATION_SUMMARY.md](./RECONFIGURATION_SUMMARY.md) | 本次重新配置的总结和验证 |

---

## 🎯 按场景选择文档

### 场景 1：我是新用户，想快速了解

**推荐阅读顺序：**
1. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 5 分钟快速入门
2. [USAGE_GUIDE.md 快速开始部分](./USAGE_GUIDE.md#快速开始) - 5 分钟快速配置
3. [examples/movie_catalog.json](./examples/movie_catalog.json) - 查看实际配置示例

**预期时间：** 15 分钟

---

### 场景 2：我需要配置实际的数据同步

**推荐阅读顺序：**
1. [CONNECTOR_CONFIGURATION.md](./CONNECTOR_CONFIGURATION.md) - 了解所有配置参数
2. [USAGE_GUIDE.md 详细配置步骤](./USAGE_GUIDE.md#详细配置步骤) - 按步骤配置
3. [examples/configuration_examples.py](./examples/configuration_examples.py) - 参考代码示例

**预期时间：** 30 分钟

---

### 场景 3：同步失败，我需要故障排除

**推荐阅读顺序：**
1. [QUICK_REFERENCE.md 常见错误排查](./QUICK_REFERENCE.md#常见错误排查) - 快速查找
2. [USAGE_GUIDE.md 故障排除](./USAGE_GUIDE.md#故障排除) - 详细解决方案
3. [TABLE_MATCH_INSERT_GUIDE.md 常见错误](./TABLE_MATCH_INSERT_GUIDE.md#常见错误及解决方案) - 语法相关问题

**预期时间：** 10 分钟

---

### 场景 4：我需要理解 GQL 语法和生成逻辑

**推荐阅读顺序：**
1. [TABLE_MATCH_INSERT_GUIDE.md](./TABLE_MATCH_INSERT_GUIDE.md) - 完整的语法指南
2. [CONNECTOR_CONFIGURATION.md 示例部分](./CONNECTOR_CONFIGURATION.md#生成的-gql-语句示例) - 实际生成的 GQL
3. [examples/configuration_examples.py](./examples/configuration_examples.py) - 查看 GQL 生成函数

**预期时间：** 20 分钟

---

### 场景 5：我正在开发或维护 Connector

**推荐阅读顺序：**
1. [README.md](./README.md) - 项目结构和集成方式
2. [RECONFIGURATION_SUMMARY.md](./RECONFIGURATION_SUMMARY.md) - 架构和组件验证
3. [CONNECTOR_CONFIGURATION.md](./CONNECTOR_CONFIGURATION.md) - 配置参考
4. [TABLE_MATCH_INSERT_GUIDE.md](./TABLE_MATCH_INSERT_GUIDE.md) - GQL 实现细节

**预期时间：** 1 小时

---

## 🔍 按主题查找

### Connection 配置（连接层）
- [QUICK_REFERENCE.md - Connection 配置](./QUICK_REFERENCE.md#connection-配置连接层)
- [CONNECTOR_CONFIGURATION.md - Connection Configuration](./CONNECTOR_CONFIGURATION.md#connection-configuration)
- [USAGE_GUIDE.md - 步骤 2：配置 Connection](./USAGE_GUIDE.md#步骤-2在-airbyte-中配置-connection)

### Destination 配置（目标层）
- [QUICK_REFERENCE.md - Destination 配置](./QUICK_REFERENCE.md#destination-配置目标层)
- [CONNECTOR_CONFIGURATION.md - Destination Configuration](./CONNECTOR_CONFIGURATION.md#destination-configuration)
- [USAGE_GUIDE.md - 步骤 3：配置 Destination](./USAGE_GUIDE.md#步骤-3配置-destination-参数)

### Catalog 配置（数据映射）
- [QUICK_REFERENCE.md - Catalog 配置](./QUICK_REFERENCE.md#catalog-配置顶点映射)
- [CONNECTOR_CONFIGURATION.md - Catalog 配置](./CONNECTOR_CONFIGURATION.md#catalog-配置数据映射)
- [USAGE_GUIDE.md - 步骤 4：配置数据映射](./USAGE_GUIDE.md#步骤-4配置数据映射catalog)
- [examples/movie_catalog.json](./examples/movie_catalog.json) - 实际示例

### 顶点映射
- [CONNECTOR_CONFIGURATION.md - 顶点映射配置](./CONNECTOR_CONFIGURATION.md#顶点映射配置)
- [USAGE_GUIDE.md - 配置顶点映射](./USAGE_GUIDE.md#42-配置顶点映射)
- [examples/configuration_examples.py - ACTOR_STREAM_CONFIG](./examples/configuration_examples.py)

### 边映射
- [CONNECTOR_CONFIGURATION.md - 边映射配置](./CONNECTOR_CONFIGURATION.md#边映射配置)
- [USAGE_GUIDE.md - 配置边映射](./USAGE_GUIDE.md#43-配置边映射)
- [examples/configuration_examples.py - ACTED_IN_STREAM_CONFIG](./examples/configuration_examples.py)
- [TABLE_MATCH_INSERT_GUIDE.md - 边插入](./TABLE_MATCH_INSERT_GUIDE.md#边插入)

### 数据类型转换
- [QUICK_REFERENCE.md - 数据类型转换](./QUICK_REFERENCE.md#数据类型转换)
- [CONNECTOR_CONFIGURATION.md - 数据类型转换](./CONNECTOR_CONFIGURATION.md#数据类型转换)
- [TABLE_MATCH_INSERT_GUIDE.md - 数据类型格式化](./TABLE_MATCH_INSERT_GUIDE.md#数据类型格式化规则)

### 写入模式
- [QUICK_REFERENCE.md - 冲突处理模式](./QUICK_REFERENCE.md#冲突处理模式)
- [CONNECTOR_CONFIGURATION.md - 写入模式](./CONNECTOR_CONFIGURATION.md#四种冲突处理模式)
- [TABLE_MATCH_INSERT_GUIDE.md - 冲突处理](./TABLE_MATCH_INSERT_GUIDE.md#冲突处理)
- [USAGE_GUIDE.md - 选择写入模式](./USAGE_GUIDE.md#32-选择写入模式)

### 故障排除
- [QUICK_REFERENCE.md - 常见错误排查](./QUICK_REFERENCE.md#常见错误排查)
- [USAGE_GUIDE.md - 故障排除](./USAGE_GUIDE.md#故障排除)
- [TABLE_MATCH_INSERT_GUIDE.md - 常见错误](./TABLE_MATCH_INSERT_GUIDE.md#常见错误及解决方案)

---

## 📞 获取帮助

### 问题类型 → 推荐查看

| 问题 | 推荐文档 |
|------|---------|
| "连接失败" | [故障排除 - 连接问题](./USAGE_GUIDE.md#连接问题) |
| "数据没有插入" | [故障排除 - 数据插入问题](./USAGE_GUIDE.md#数据插入问题) |
| "字段值为 NULL" | [故障排除 - 数据插入问题](./USAGE_GUIDE.md#问题数据插入成功但字段值为-null) |
| "同步很慢" | [故障排除 - 性能问题](./USAGE_GUIDE.md#性能问题) |
| "配置很复杂" | [配置最佳实践](./USAGE_GUIDE.md#配置最佳实践) |
| "不知道选哪个写入模式" | [写入模式选择](./USAGE_GUIDE.md#5-写入模式选择) |
| "GQL 语法错误" | [TABLE_MATCH_INSERT_GUIDE.md](./TABLE_MATCH_INSERT_GUIDE.md) |

---

## 📝 文档特点

- ✅ **清晰的结构** - 所有文档都有目录和跳转链接
- ✅ **实际示例** - 包含可直接使用的配置代码和 JSON
- ✅ **分级说明** - 从快速开始到深入指南，逐级递进
- ✅ **按场景组织** - 不同用户可快速找到相关内容
- ✅ **故障排除** - 常见问题和解决方案完整列出
- ✅ **索引完善** - 本文档提供多个切入点

---

## 🎓 学习路径建议

### 初学者路径（推荐）
```
QUICK_REFERENCE.md (5 min)
    ↓
USAGE_GUIDE.md - 快速开始 (10 min)
    ↓
examples/movie_catalog.json (查看实例)
    ↓
USAGE_GUIDE.md - 详细配置 (30 min)
    ↓
实际配置和测试
```
**总时间：** ~50 分钟

### 进阶路径
```
CONNECTOR_CONFIGURATION.md (完整参考)
    ↓
TABLE_MATCH_INSERT_GUIDE.md (语法深入)
    ↓
examples/configuration_examples.py (代码示例)
    ↓
USAGE_GUIDE.md - 最佳实践 (深入优化)
```
**总时间：** ~1.5 小时

### 开发者路径
```
README.md (项目结构)
    ↓
RECONFIGURATION_SUMMARY.md (验证清单)
    ↓
CONNECTOR_CONFIGURATION.md (完整参考)
    ↓
TABLE_MATCH_INSERT_GUIDE.md (实现细节)
    ↓
代码审查和测试
```
**总时间：** ~2 小时

---

## 版本信息

| 项目 | 版本 |
|------|------|
| Connector | 1.0 |
| Yueshu 数据库 | 5.2.0 |
| Python 客户端 | nebula5-python |
| 文档更新时间 | 2024 年 1 月 15 日 |

---

## 快速链接

- 🏠 [项目首页](./README.md)
- ⚡ [5 分钟快速参考](./QUICK_REFERENCE.md)
- 📖 [详细使用指南](./USAGE_GUIDE.md)
- 📚 [完整配置参考](./CONNECTOR_CONFIGURATION.md)
- 🔧 [GQL 语法指南](./TABLE_MATCH_INSERT_GUIDE.md)
- 💻 [代码示例](./examples/configuration_examples.py)
- 🎯 [Catalog 示例](./examples/movie_catalog.json)
- ✓ [重新配置总结](./RECONFIGURATION_SUMMARY.md)

---

**需要帮助？** 查看[USAGE_GUIDE.md 常见问题部分](./USAGE_GUIDE.md#常见问题)或查阅本索引的"按主题查找"部分。
