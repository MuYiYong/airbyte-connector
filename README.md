# 悦数图数据库 5.2 Airbyte 连接器（Source + Destination）

本项目实现了同时支持 Source 与 Destination 的 Airbyte 连接器，使用 `nebula5-python` SDK 连接悦数图数据库 5.2。

## 目录
- `src/yueshu_airbyte_connector`：连接器实现
- `scripts/validate_connection.py`：连接验证脚本
- `Dockerfile.source` / `Dockerfile.destination`：Docker 构建入口

## 配置说明（通用）
连接器配置（仅连接信息）：
- `hosts`（仅支持 `host:port` 形式，可多组）
- `username` / `password`（默认 `root` / `root`）

连接级别配置（Catalog/stream config）：
- `graph`：图名（可选）
- `setup_queries`：预置语句（可选，首次使用该 stream 时执行）
- Source：`read_query`
- Destination：`write_query_template` 与 `write_mode`

### Source 配置
读取结果会以单条记录输出，字段包含 `payload`（结果字符串）、`query` 与 `index`。

示例连接配置文件：`configs/source.sample.json`。
示例 Catalog 配置文件：`configs/source.catalog.sample.json`。

示例查询（来自本地文档中的 MATCH 示例）：
- `SESSION SET GRAPH movie`
- `MATCH (v) RETURN v LIMIT 5`
- `MATCH ()-[e]->() RETURN e LIMIT 5`

### Destination 配置

**推荐使用 Mapping 配置方式**（自动生成 GQL）

连接器支持两种配置方式：
1. **Mapping-based**（推荐）- 通过配置映射关系自动生成 GQL
2. **Template-based**（传统）- 手动编写 GQL 模板（仅向后兼容）

#### Mapping 配置方式

##### 点表映射（Vertex）
配置源表到图数据库点表的映射：
- 选择源表字段作为点的主键
- 选择其他字段作为点的属性（可选）
- 支持数据类型转换（date, datetime, timestamp）

##### 边表映射（Edge）
配置源表到图数据库边表的映射：
- 选择源表字段作为起点主键
- 选择源表字段作为终点主键
- 选择源表字段作为多边键/ranking（可选）
- 选择其他字段作为边的属性（可选）
- 支持数据类型转换

#### Write Mode 更新模式
`write_mode` 支持以下更新模式：
- `insert` - 仅插入，记录已存在则报错
- `insert or replace` - 插入或替换整条记录
- `insert or ignore` - 插入或忽略（默认）
- `insert or update` - 插入或合并更新属性

写入时会自动使用 **TABLE INSERT** 或 **TABLE MATCH INSERT** 语法，并应用配置的 `write_mode`。

#### 配置文件示例

示例连接配置文件：`configs/destination.sample.json`

示例 Catalog 配置文件（推荐）：
- `configs/destination.catalog.sample.json` - 标准 mapping 格式
- `configs/destination.catalog.flat.json` - 扁平化 mapping 格式
- `configs/destination.catalog.optimized.json` - 完整示例

> 💡 **提示**：请确保目标图空间中已创建对应的点类型和边类型（Schema）。

## 运行方式（本地）
入口命令：`yueshu-airbyte`。

示例：
- 读取 Source 规范：`yueshu-airbyte --connector-type source --command spec`
- 校验连接：`yueshu-airbyte --connector-type source --command check --config <config.json>`
- 读取数据：`yueshu-airbyte --connector-type source --command read --config <config.json>`
- 写入数据：`yueshu-airbyte --connector-type destination --command write --config <config.json>`

## Docker
- Source 镜像入口使用 `CONNECTOR_TYPE=source`
- Destination 镜像入口使用 `CONNECTOR_TYPE=destination`

## 在 Airbyte 中集成此自定义 Connector
> 说明：以下以 **Docker 镜像方式** 集成为例，适用于 Airbyte OSS。

### 1) 构建镜像
在本仓库根目录执行：
- Source 镜像：`docker build -f Dockerfile.source -t yueshu-airbyte-source:local .`
- Destination 镜像：`docker build -f Dockerfile.destination -t yueshu-airbyte-destination:local .`

### 2) 将镜像接入 Airbyte
在启动 Airbyte 之前，确保 Airbyte 所在的 Docker 环境能访问到上述镜像：
- 方式 A：本机 `docker` 直接构建（同一 Docker daemon）
- 方式 B：推送到私有仓库后，在 Airbyte 主机上拉取

### 3) 配置 Airbyte 识别自定义 Connector
#### 方式 A：`docker-compose` 环境
在 Airbyte 的 `docker-compose` 环境中，设置环境变量 `AIRBYTE_CUSTOM_CONNECTOR_CONFIGS`，示例：

Source：
```json
[
	{
		"name": "yueshu-airbyte-source",
		"dockerRepository": "yueshu-airbyte-source",
		"dockerImageTag": "local"
	}
]
```

Destination：
```json
[
	{
		"name": "yueshu-airbyte-destination",
		"dockerRepository": "yueshu-airbyte-destination",
		"dockerImageTag": "local"
	}
]
```

> 如果需要同时注册 Source 与 Destination，可将两项合并到同一个 JSON 数组中。

#### 方式 B：`abctl`（Kubernetes）环境
`abctl` 安装不会生成 `docker-compose`。请在 `abctl` 的 values 中为 `airbyte-server`（必要时也为 `airbyte-worker`）添加环境变量。

**abctl 已安装（本地 kind 集群）完整步骤：**
1. 安装 `kind` 命令行（若提示 `kind not found`）：
	- 示例：`brew install kind`
2. 将本地镜像加载到 kind 集群：
	- `kind load docker-image yueshu-airbyte-source:local --name airbyte-abctl`
	- `kind load docker-image yueshu-airbyte-destination:local --name airbyte-abctl`
3. 准备 values 文件，添加 `AIRBYTE_CUSTOM_CONNECTOR_CONFIGS`：
4. 重新应用配置：`abctl local install --values <your-values.yaml>`
	- 若提示已安装但配置未生效，可先 `abctl local uninstall` 再执行安装。

示例 values（片段）：
```yaml
airbyte-server:
  extraEnv:
    - name: AIRBYTE_CUSTOM_CONNECTOR_CONFIGS
      value: >-
        [{"name":"yueshu-airbyte-source","dockerRepository":"yueshu-airbyte-source","dockerImageTag":"local"},
         {"name":"yueshu-airbyte-destination","dockerRepository":"yueshu-airbyte-destination","dockerImageTag":"local"}]

airbyte-worker:
  extraEnv:
    - name: AIRBYTE_CUSTOM_CONNECTOR_CONFIGS
      value: >-
        [{"name":"yueshu-airbyte-source","dockerRepository":"yueshu-airbyte-source","dockerImageTag":"local"},
         {"name":"yueshu-airbyte-destination","dockerRepository":"yueshu-airbyte-destination","dockerImageTag":"local"}]
```

应用方式根据你的 `abctl` 版本可能是：
- `abctl local install --values <your-values.yaml>`
- 若提示已安装且配置未生效：`abctl local uninstall` 后重新 `install`

> 注意：若非 kind 集群，请改用对应的镜像加载方式（如 minikube/k3d 或私有 registry）。

### 4) 在 UI 中创建连接
1. 打开 Airbyte UI，创建 **Source** 或 **Destination**。
2. 在连接器列表中选择上一步注册的 `yueshu-airbyte-source` 或 `yueshu-airbyte-destination`。
3. 按照 `configs/source.sample.json` 或 `configs/destination.sample.json` 的字段填写连接配置。
4. 在连接的 Catalog/stream config 中填写 `graph`、`setup_queries` 与读/写模板（参考 `configs/*.catalog.sample.json`）。

> 重要：Airbyte UI 的 **Select streams** / **Configure connection** 页面默认不会展示自定义的 stream config 字段。
> 请点击 **Edit JSON**，在 Catalog 中为每个 stream 的 `config` 填写映射信息。

**Edit JSON 示例（Destination - Mapping 格式）**：

点表映射示例：
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
						{"source_field": "name", "dest_field": "name"},
						{"source_field": "birth_date", "dest_field": "birthDate", "transform": "date"}
					]
				},
				"write_mode": "insert or replace"
			}
		}
	]
}
```

边表映射示例：
```json
{
	"streams": [
		{
			"stream": {"name": "acts"},
			"config": {
				"graph": "movie",
				"mapping": {
					"type": "edge",
					"label": "Act",
					"src_vertex": {
						"label": "Actor",
						"primary_key": {"source_field": "actor_id", "dest_field": "id"}
					},
					"dst_vertex": {
						"label": "Movie",
						"primary_key": {"source_field": "movie_id", "dest_field": "id"}
					},
					"multiedge_key": {"source_field": "role_id"},
					"properties": [
						{"source_field": "role_name", "dest_field": "roleName"}
					]
				},
				"write_mode": "insert or update"
			}
		}
	]
}
```

**Edit JSON 示例（Source）**：
```json
{
	"streams": [
		{
			"stream": {"name": "edges_sample"},
			"config": {
				"graph": "movie",
				"setup_queries": ["SESSION SET GRAPH movie"],
				"read_query": "MATCH ()-[e]->() RETURN e LIMIT 5"
			}
		}
	]
}
```
4. 点击 **Test** 验证连接，创建并运行同步任务。

### 5) 常见问题
- **找不到自定义连接器**：确认 `AIRBYTE_CUSTOM_CONNECTOR_CONFIGS` 已生效并重启 Airbyte。
- **镜像拉取失败**：检查镜像是否存在于 Airbyte 主机可访问的 registry/daemon 中。
- **配置校验失败**：先用本地命令 `yueshu-airbyte --connector-type ... --command check` 验证配置。

## 验证测试
已提供验证脚本：`scripts/validate_connection.py`。
脚本默认使用以下环境变量（可覆盖）：
- `YUESHU_HOST`（默认 192.168.15.240）
- `YUESHU_PORT`（默认 39669）
- `YUESHU_USERNAME`（默认 root）
- `YUESHU_PASSWORD`（默认 Nebula123）
- `YUESHU_GRAPH`（可选）
- `YUESHU_CHECK_QUERY`（默认 `SHOW CURRENT_USER`）
