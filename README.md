# 悦数图数据库 5.2 Airbyte 连接器（Source + Destination）

本项目实现了同时支持 Source 与 Destination 的 Airbyte 连接器，使用 `nebula5-python` SDK 连接悦数图数据库 5.2。

## 目录
- `src/yueshu_airbyte_connector`：连接器实现
- `scripts/validate_connection.py`：连接验证脚本
- `Dockerfile.source` / `Dockerfile.destination`：Docker 构建入口

## 配置说明（通用）
通用连接字段：
- `host` / `port`
- `username` / `password`
- `graph`（可选，若需要指定工作图）
- `check_query`（可选，默认 `SHOW CURRENT_USER`）
- `setup_queries`（可选，连接后执行的初始化语句列表）

### Source 配置
额外字段：
- `read_queries`: 读取查询数组，每项包含 `name` 与 `query`

读取结果会以单条记录输出，字段包含 `payload`（结果字符串）、`query` 与 `index`。

示例配置文件：`configs/source.sample.json`（使用图 `movie`）。

示例查询（来自本地文档中的 MATCH 示例）：
- `SESSION SET GRAPH movie`
- `MATCH (v) RETURN v LIMIT 5`
- `MATCH ()-[e]->() RETURN e LIMIT 5`

### Destination 配置
额外字段：
- `write_queries`: 写入规则数组，每项包含 `stream` 与 `query_template`，可选 `write_mode`

`write_mode` 支持以下更新模式：
- `insert`
- `insert or replace`
- `insert or ignore`（默认）
- `insert or update`

写入时会优先使用 **table insert** 或 **table match insert** 语法；若模板为普通 `INSERT`/`MATCH ... INSERT`，会自动补齐为 `TABLE INSERT`/`TABLE MATCH ... INSERT` 并应用 `write_mode`。

当接收到对应 `stream` 的 `RECORD` 消息时，会把 `query_template` 中的 `{字段名}` 替换为记录中的字段值并执行。

示例配置文件：`configs/destination.sample.json`（使用图 `movie`）。

示例写入语句（来自本地文档中的 INSERT 示例）：
- `SESSION SET GRAPH movie`
- `TABLE INSERT (@Actor{id:{id}, name:"{name}", birthDate:date("{birth_date}")})`
- `TABLE INSERT (@Movie{id:{id}, name:"{name}"})`
- `TABLE MATCH (n@Actor{id:{src_id}}), (m@Movie{id:{dst_id}}) INSERT (n)-[@Act]->(m)`

提示：请确保图 `movie` 中已存在对应点类型/标签与边类型（如 `Actor`、`Movie`、`Act`）。

写后验证（示例查询）：
- `SESSION SET GRAPH movie`
- `MATCH (n@Actor{id:900001}) RETURN n`
- `MATCH (m@Movie{id:10003}) RETURN m`
- `MATCH (n@Actor{id:900001})-[e@Act]->(m@Movie{id:10003}) RETURN e`

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
3. 按照 `configs/source.sample.json` 或 `configs/destination.sample.json` 的字段填写配置。
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
