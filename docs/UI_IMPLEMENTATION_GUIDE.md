# UI 映射配置实现指南

本文档详细说明如何在 Airbyte 中实现可视化的映射配置 UI。

---

## 一、方案概述

### 目标

将复杂的 JSON 映射配置转换为用户友好的可视化表单，让用户通过 UI 界面进行字段映射配置，而不是手动编辑 JSON。

### 实现方式

1. **JSON Schema 增强**：使用 `airbyte_ui` 扩展字段定义 UI 组件类型
2. **条件渲染**：使用 `if-then-else` 和 `allOf` 实现动态表单
3. **自定义 UI 组件**：开发 React 组件渲染配置表单
4. **字段自动发现**：从源 stream schema 中自动获取可选字段列表

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   Airbyte UI Layer                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Stream Config Form (React Component)            │  │
│  │  - 读取 JSON Schema                              │  │
│  │  - 动态渲染表单字段                              │  │
│  │  - 提供字段选择器                                │  │
│  │  - 支持条件显示                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                          ↓                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Schema Resolver                                 │  │
│  │  - 解析 stream_config_ui_spec.json               │  │
│  │  - 处理 if-then-else 逻辑                        │  │
│  │  - 提供字段列表                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                          ↓                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Form Data → JSON Config                        │  │
│  │  - 转换表单数据为 connector 所需格式             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│               Airbyte Connector (Backend)               │
│  - 接收 JSON 配置                                       │
│  - 生成 GQL 语句                                        │
│  - 执行数据同步                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户操作 UI 表单
    ↓
表单数据收集
    ↓
验证表单数据
    ↓
转换为 JSON 配置
    ↓
发送到 Airbyte 后端
    ↓
Connector 解析配置
    ↓
生成 GQL 并执行
```

---

## 三、JSON Schema 设计

### 3.1 使用 `airbyte_ui` 扩展

在标准 JSON Schema 中添加 `airbyte_ui` 字段来指定 UI 渲染方式：

```json
{
  "type": "string",
  "title": "图空间",
  "airbyte_ui": {
    "type": "text",
    "placeholder": "例如: movie"
  }
}
```

### 3.2 支持的 UI 组件类型

| UI 类型 | 说明 | Schema 示例 |
|---------|------|-------------|
| `text` | 文本输入框 | `{"type": "text", "placeholder": "..."}` |
| `select` | 下拉选择框 | `{"type": "select", "options": [...]}` |
| `radio` | 单选按钮组 | `{"type": "radio", "options": [...]}` |
| `checkbox` | 复选框 | `{"type": "checkbox"}` |
| `array_editor` | 数组编辑器 | `{"type": "array_editor", "addButtonText": "..."}` |

### 3.3 字段自动填充

使用 `source: "stream_fields"` 从源 stream schema 中自动获取字段列表：

```json
{
  "source_field": {
    "type": "string",
    "title": "源表字段",
    "airbyte_ui": {
      "type": "select",
      "source": "stream_fields"
    }
  }
}
```

### 3.4 条件渲染

使用 `if-then-else` 实现根据用户选择动态显示字段：

```json
{
  "if": {
    "properties": {
      "mapping_type": {"const": "vertex"}
    }
  },
  "then": {
    "properties": {
      "vertex_label": {...},
      "vertex_primary_key": {...}
    },
    "required": ["vertex_label", "vertex_primary_key"]
  }
}
```

---

## 四、React 组件实现

### 4.1 主组件结构

```jsx
import React, { useState, useEffect } from 'react';

const StreamMappingConfig = ({ streamSchema, onConfigChange }) => {
  const [config, setConfig] = useState({
    graph: '',
    mapping_type: 'vertex',
    write_mode: 'insert or ignore'
  });

  const [streamFields, setStreamFields] = useState([]);

  // 从 stream schema 中提取字段列表
  useEffect(() => {
    if (streamSchema && streamSchema.properties) {
      const fields = Object.keys(streamSchema.properties);
      setStreamFields(fields);
    }
  }, [streamSchema]);

  const handleMappingTypeChange = (type) => {
    setConfig({
      ...config,
      mapping_type: type
    });
  };

  return (
    <div className="stream-mapping-config">
      <GraphSelector value={config.graph} onChange={...} />
      <MappingTypeSelector value={config.mapping_type} onChange={handleMappingTypeChange} />
      
      {config.mapping_type === 'vertex' && (
        <VertexConfig 
          config={config}
          streamFields={streamFields}
          onChange={setConfig}
        />
      )}
      
      {config.mapping_type === 'edge' && (
        <EdgeConfig 
          config={config}
          streamFields={streamFields}
          onChange={setConfig}
        />
      )}
      
      <WriteModeSelector value={config.write_mode} onChange={...} />
    </div>
  );
};
```

### 4.2 点表配置组件

```jsx
const VertexConfig = ({ config, streamFields, onChange }) => {
  const [properties, setProperties] = useState([]);

  const addProperty = () => {
    setProperties([
      ...properties,
      { source_field: '', dest_field: '', transform: '' }
    ]);
  };

  return (
    <div className="vertex-config">
      <TextInput
        label="点类型标签"
        value={config.vertex_label}
        onChange={(value) => onChange({...config, vertex_label: value})}
      />
      
      <PrimaryKeyMapping
        streamFields={streamFields}
        value={config.vertex_primary_key}
        onChange={(value) => onChange({...config, vertex_primary_key: value})}
      />
      
      <PropertyList
        properties={properties}
        streamFields={streamFields}
        onAdd={addProperty}
        onChange={setProperties}
      />
    </div>
  );
};
```

### 4.3 边表配置组件

```jsx
const EdgeConfig = ({ config, streamFields, onChange }) => {
  const [multiedgeEnabled, setMultiedgeEnabled] = useState(false);

  return (
    <div className="edge-config">
      <TextInput
        label="边类型标签"
        value={config.edge_label}
        onChange={(value) => onChange({...config, edge_label: value})}
      />
      
      <VertexEndpointConfig
        label="起点配置"
        streamFields={streamFields}
        value={config.edge_src_vertex}
        onChange={(value) => onChange({...config, edge_src_vertex: value})}
      />
      
      <VertexEndpointConfig
        label="终点配置"
        streamFields={streamFields}
        value={config.edge_dst_vertex}
        onChange={(value) => onChange({...config, edge_dst_vertex: value})}
      />
      
      <MultiedgeConfig
        enabled={multiedgeEnabled}
        streamFields={streamFields}
        onEnabledChange={setMultiedgeEnabled}
        onChange={(value) => onChange({...config, edge_multiedge_key: value})}
      />
      
      <PropertyList
        properties={config.edge_properties || []}
        streamFields={streamFields}
        onChange={(value) => onChange({...config, edge_properties: value})}
      />
    </div>
  );
};
```

### 4.4 通用字段选择器

```jsx
const FieldSelector = ({ label, options, value, onChange }) => {
  return (
    <div className="field-selector">
      <label>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">请选择字段</option>
        {options.map(field => (
          <option key={field} value={field}>{field}</option>
        ))}
      </select>
    </div>
  );
};
```

### 4.5 属性列表编辑器

```jsx
const PropertyList = ({ properties, streamFields, onAdd, onChange }) => {
  const removeProperty = (index) => {
    onChange(properties.filter((_, i) => i !== index));
  };

  const updateProperty = (index, field, value) => {
    const updated = [...properties];
    updated[index][field] = value;
    onChange(updated);
  };

  return (
    <div className="property-list">
      <label>属性字段映射（可选）</label>
      {properties.map((prop, index) => (
        <div key={index} className="property-item">
          <div className="property-header">
            <span>属性 {index + 1}</span>
            <button onClick={() => removeProperty(index)}>删除</button>
          </div>
          <div className="property-fields">
            <FieldSelector
              label="源表字段"
              options={streamFields}
              value={prop.source_field}
              onChange={(v) => updateProperty(index, 'source_field', v)}
            />
            <TextInput
              label="目标属性名"
              value={prop.dest_field}
              onChange={(v) => updateProperty(index, 'dest_field', v)}
            />
            <select
              value={prop.transform}
              onChange={(e) => updateProperty(index, 'transform', e.target.value)}
            >
              <option value="">无转换</option>
              <option value="date">Date</option>
              <option value="datetime">DateTime</option>
              <option value="timestamp">Timestamp</option>
            </select>
          </div>
        </div>
      ))}
      <button onClick={onAdd} className="add-button">+ 添加属性字段</button>
    </div>
  );
};
```

---

## 五、配置数据转换

### 5.1 UI 表单数据 → JSON 配置

需要实现一个转换函数，将 UI 表单数据转换为 connector 期望的 JSON 格式：

```javascript
function transformUIConfigToConnectorConfig(uiConfig) {
  const baseConfig = {
    graph: uiConfig.graph,
    write_mode: uiConfig.write_mode
  };

  if (uiConfig.mapping_type === 'vertex') {
    return {
      ...baseConfig,
      mapping: {
        type: 'vertex',
        label: uiConfig.vertex_label,
        primary_key: {
          source_field: uiConfig.vertex_primary_key.source_field,
          dest_field: uiConfig.vertex_primary_key.dest_field
        },
        properties: (uiConfig.vertex_properties || [])
          .filter(p => p.source_field && p.dest_field)
          .map(p => ({
            source_field: p.source_field,
            dest_field: p.dest_field,
            ...(p.transform && { transform: p.transform })
          }))
      }
    };
  } else {
    return {
      ...baseConfig,
      mapping: {
        type: 'edge',
        label: uiConfig.edge_label,
        src_vertex: {
          label: uiConfig.edge_src_vertex.label,
          primary_key: {
            source_field: uiConfig.edge_src_vertex.primary_key_source,
            dest_field: uiConfig.edge_src_vertex.primary_key_dest
          }
        },
        dst_vertex: {
          label: uiConfig.edge_dst_vertex.label,
          primary_key: {
            source_field: uiConfig.edge_dst_vertex.primary_key_source,
            dest_field: uiConfig.edge_dst_vertex.primary_key_dest
          }
        },
        ...(uiConfig.edge_multiedge_key?.enabled && {
          multiedge_key: {
            source_field: uiConfig.edge_multiedge_key.source_field
          }
        }),
        properties: (uiConfig.edge_properties || [])
          .filter(p => p.source_field && p.dest_field)
          .map(p => ({
            source_field: p.source_field,
            dest_field: p.dest_field,
            ...(p.transform && { transform: p.transform })
          }))
      }
    };
  }
}
```

### 5.2 JSON 配置 → UI 表单数据

反向转换，用于编辑已有配置：

```javascript
function transformConnectorConfigToUIConfig(connectorConfig) {
  const baseConfig = {
    graph: connectorConfig.graph,
    write_mode: connectorConfig.write_mode || 'insert or ignore',
    mapping_type: connectorConfig.mapping.type
  };

  if (connectorConfig.mapping.type === 'vertex') {
    return {
      ...baseConfig,
      vertex_label: connectorConfig.mapping.label,
      vertex_primary_key: connectorConfig.mapping.primary_key,
      vertex_properties: connectorConfig.mapping.properties || []
    };
  } else {
    return {
      ...baseConfig,
      edge_label: connectorConfig.mapping.label,
      edge_src_vertex: {
        label: connectorConfig.mapping.src_vertex.label,
        primary_key_source: connectorConfig.mapping.src_vertex.primary_key.source_field,
        primary_key_dest: connectorConfig.mapping.src_vertex.primary_key.dest_field
      },
      edge_dst_vertex: {
        label: connectorConfig.mapping.dst_vertex.label,
        primary_key_source: connectorConfig.mapping.dst_vertex.primary_key.source_field,
        primary_key_dest: connectorConfig.mapping.dst_vertex.primary_key.dest_field
      },
      edge_multiedge_key: connectorConfig.mapping.multiedge_key
        ? {
            enabled: true,
            source_field: connectorConfig.mapping.multiedge_key.source_field
          }
        : { enabled: false },
      edge_properties: connectorConfig.mapping.properties || []
    };
  }
}
```

---

## 六、集成到 Airbyte

### 6.1 在 Connector 中注册 UI Schema

修改 connector 的 `spec()` 方法，添加 stream configuration schema：

```python
def spec(self) -> ConnectorSpecification:
    return ConnectorSpecification(
        connectionSpecification=self._load_json_schema("destination_spec.json"),
        streamConfigSchema=self._load_json_schema("stream_config_ui_spec.json")
    )
```

### 6.2 Airbyte UI 路由配置

在 Airbyte 前端注册自定义 UI 组件：

```typescript
// airbyte-webapp/src/components/connectors/YueshuDestination/index.tsx
import { StreamMappingConfig } from './StreamMappingConfig';

export const YueshuDestinationConfig = {
  connectorType: 'destination',
  connectorName: 'yueshu-airbyte-destination',
  streamConfigComponent: StreamMappingConfig
};
```

### 6.3 表单验证

实现表单验证逻辑：

```javascript
function validateConfig(config) {
  const errors = {};

  if (!config.graph) {
    errors.graph = '图空间名称不能为空';
  }

  if (config.mapping_type === 'vertex') {
    if (!config.vertex_label) {
      errors.vertex_label = '点类型标签不能为空';
    }
    if (!config.vertex_primary_key?.source_field) {
      errors.vertex_primary_key = '必须选择源表主键字段';
    }
  } else if (config.mapping_type === 'edge') {
    if (!config.edge_label) {
      errors.edge_label = '边类型标签不能为空';
    }
    if (!config.edge_src_vertex?.label) {
      errors.edge_src_label = '起点类型不能为空';
    }
    if (!config.edge_dst_vertex?.label) {
      errors.edge_dst_label = '终点类型不能为空';
    }
  }

  return Object.keys(errors).length > 0 ? errors : null;
}
```

---

## 七、UI 原型预览

### 7.1 查看 HTML 原型

打开文件 [`ui/mapping_config_ui.html`](file:///Users/muyi/Documents/Vesoft/workspace/airbyte-connector/ui/mapping_config_ui.html) 可以在浏览器中查看交互式 UI 原型。

原型包含：
- ✅ 图空间输入
- ✅ 映射类型选择（点表/边表）
- ✅ 动态表单切换
- ✅ 字段选择器
- ✅ 属性列表编辑器
- ✅ 多边键配置
- ✅ 写入模式选择

### 7.2 运行原型

```bash
# 在浏览器中打开
open ui/mapping_config_ui.html

# 或使用 HTTP 服务器
cd ui
python3 -m http.server 8080
# 然后访问 http://localhost:8080/mapping_config_ui.html
```

---

## 八、实现路线图

### Phase 1: 基础 UI 框架（1-2 周）
- [ ] 创建 React 组件框架
- [ ] 实现基础表单字段（文本、选择器）
- [ ] 实现映射类型切换

### Phase 2: 高级功能（2-3 周）
- [ ] 实现属性列表编辑器
- [ ] 实现字段自动发现
- [ ] 实现条件渲染逻辑
- [ ] 添加表单验证

### Phase 3: 集成与测试（1-2 周）
- [ ] 集成到 Airbyte UI
- [ ] 实现配置数据转换
- [ ] 端到端测试
- [ ] UI/UX 优化

### Phase 4: 文档与发布（1 周）
- [ ] 编写用户文档
- [ ] 录制演示视频
- [ ] 发布到 Airbyte 市场

---

## 九、技术栈建议

### 前端技术
- **框架**: React 18+
- **UI 库**: Ant Design 或 Material-UI
- **表单管理**: React Hook Form
- **验证**: Yup 或 Zod
- **样式**: CSS Modules 或 Styled Components

### 开发工具
- **TypeScript**: 类型安全
- **ESLint**: 代码规范
- **Prettier**: 代码格式化
- **Storybook**: 组件开发与测试

---

## 十、最佳实践

### 10.1 用户体验
1. **渐进式披露**: 根据用户选择逐步显示相关字段
2. **即时验证**: 在用户输入时提供即时反馈
3. **智能默认值**: 提供合理的默认配置
4. **帮助提示**: 为每个字段提供清晰的说明
5. **错误提示**: 使用友好的错误消息

### 10.2 性能优化
1. **懒加载**: 大型表单分区域加载
2. **防抖/节流**: 优化字段验证
3. **虚拟滚动**: 处理大量字段选项
4. **缓存**: 缓存 stream schema 数据

### 10.3 可访问性
1. **键盘导航**: 支持完整的键盘操作
2. **屏幕阅读器**: 添加适当的 ARIA 标签
3. **色彩对比**: 确保文字可读性
4. **焦点管理**: 合理的焦点顺序

---

## 十一、常见问题

### Q1: 如何处理大量源表字段？

使用带搜索功能的下拉选择器，支持字段名模糊搜索。

### Q2: 如何支持批量配置？

提供批量导入功能，允许用户上传 CSV 或复制粘贴配置。

### Q3: 如何处理配置迁移？

提供配置导出/导入功能，支持在不同环境间迁移配置。

### Q4: 如何测试 UI 组件？

使用 Jest + React Testing Library 进行单元测试，使用 Cypress 进行 E2E 测试。

---

## 十二、总结

通过实现可视化的映射配置 UI，我们可以：

✅ **降低使用门槛** - 无需手写 JSON
✅ **减少配置错误** - 通过验证和约束防止错误
✅ **提升用户体验** - 直观的表单界面
✅ **提高效率** - 快速完成复杂配置

下一步可以基于提供的 HTML 原型和 React 组件示例，开始实际的 UI 开发工作。
