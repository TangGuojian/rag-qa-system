# 智能问答系统（RAG）

基于检索增强生成（RAG）的企业知识库问答系统。支持文档上传与解析、**三路混合检索**、SSE 流式输出、**答案级溯源**，并提供多知识库管理、检索链路参数全量可配置与操作审计能力。

> 面向的场景：企业内部制度、财政数据集等文档的问答查询——用户提问后，系统不仅给出答案，还会**标注每段回答来自哪份文档的哪一段原文**，解决大模型"胡说"无法核验的问题。

![Tests](https://github.com/TangGuojian/rag-qa-system/actions/workflows/test.yml/badge.svg)

---

## 快速开始（约 5 分钟）

不需要装数据库，不需要装 Node.js，也不需要改任何配置文件。
**唯一需要准备的是你自己的大模型 API Key**——下面会告诉你去哪领免费的。

### 1. 跑起来

环境要求：**Python 3.11 及以上**（CI 与测试基于 3.11）。

```bash
git clone https://github.com/TangGuojian/rag-qa-system.git
cd rag-qa-system/backend
pip install -r requirements.txt
python run_demo.py
```

> Windows 上如果 `python` 指向的不是 3.11，改用 `py -3.11 run_demo.py`；
> macOS / Linux 上通常是 `python3 run_demo.py`。

脚本会自动建库建表、创建管理员账号、启动服务并打开浏览器（默认 <http://127.0.0.1:8000>）。
数据存储默认使用内置 SQLite，向量库 ChromaDB 以嵌入式方式运行——**你的机器上不需要安装 MySQL、Neo4j、Redis 中的任何一个**。

想直接看到"有内容"的效果，可以改用：

```bash
python run_demo.py --import-demo     # 自动导入 demo_docs/ 下的 3 篇示例文档
```

> 注意：导入要调用向量化接口，因此**必须先配好 Key**（见下一步）。全新环境第一次运行会打印「跳过：尚未配置 API Key」，这是正常的——配好 Key 后重跑一次，或在界面里手动上传即可。

### 2. 第一次使用：照着点一遍

全新环境里数据库是空的（没有知识库、没有文档），请严格按这个顺序操作：

| # | 在哪 | 做什么 | 成功长什么样 |
|---|---|---|---|
| 1 | 登录页 | 用 `admin` / `admin123` 登录 | 进入首页 |
| 2 | 「个人设置」→ **AI 服务配置** | 选服务商 → 填 API Key → 点「测试连接」 | 提示连接成功 |
| 3 | 「个人设置」→ **向量服务（可选）** | **仅当你选的服务商不提供向量模型时才需要填**（见下一节表格） | 「当前生效」里能看到向量模型 |
| 4 | 「知识库」页 → **+ 新建知识库** | 起个名字，比如「公司制度」 | 列表里出现它 |
| 5 | 「知识库」页 → **+ 上传文档** | 选知识库 → 选文件（可用 `backend/demo_docs/` 下的三篇示例）→ 开始上传 | 文档状态变成「已完成」 |
| 6 | 「智能问答」页 | 勾选知识库 → 提问 | 逐字输出答案，底部带「📎 参考来源」 |

> **顺序不能反**：知识库是文档的容器，一个知识库都没有时无法上传——「开始上传」按钮会置灰，鼠标悬停会提示你缺什么。

### 3. Key 从哪来

本项目**不内置任何 API Key**。RAG 链路需要「对话模型 + 向量模型」两样，各服务商情况如下：

| 服务商 | 对话模型 | 向量模型 | 说明 |
|---|---|---|---|
| 阿里云百炼 | `qwen3.7-plus` | `text-embedding-v3` | 两样都提供，**最省事**，新用户有免费额度 |
| 硅基流动 | `Qwen/Qwen2.5-7B-Instruct` | `BAAI/bge-m3` | 两样都提供，bge-m3 免费 |
| 智谱 AI | `glm-4-flash` | `embedding-3` | 两样都提供，glm-4-flash 免费 |
| OpenAI | `gpt-4o-mini` | `text-embedding-3-small` | 国内访问需自备代理 |
| DeepSeek | `deepseek-chat` | ❌ **不提供** | 只能用于对话，向量必须另配一家 |

**最容易出现的问题**：只配了 DeepSeek 就去上传文档。DeepSeek 没有向量化接口，系统无法把文档转成向量，上传会失败并提示「DeepSeek 不提供向量化接口」。

两种解法，任选其一：

- **推荐**：换用百炼或硅基流动这类"对话 + 向量都有"的服务商，一家的 Key 就够；
- **坚持用 DeepSeek**：把「向量服务（可选）」单独填成硅基流动（地址 `https://api.siliconflow.cn/v1`，模型 `BAAI/bge-m3`，免费）。**对话和向量用不同服务商是完全支持的**，也是国内很常见的省钱搭配。

个人设置页里选好服务商后，API 地址和推荐模型名会自动带出，也可以手动改。点「获取可用模型」可以从服务商拉取真实列表，避免手写模型名出错。**换服务商不用改代码。**

### 4. 卡住了？先看这里

| 现象 | 原因与解决 |
|---|---|
| 上传按钮点不动（置灰） | 还没选知识库，或一个知识库都没建。鼠标悬停在按钮上会提示具体原因 |
| 上传后状态是「失败」 | 服务商不提供向量接口（如 DeepSeek）→ 去「向量服务（可选）」单独配一个；或 Key 余额不足 |
| 回答是空的，只有一个空气泡 | 同上。气泡里会直接写出失败原因，按提示处理 |
| 回答没有「参考来源」 | 知识库里没有命中内容，或文档还在解析中（稍等几秒刷新） |
| 提问报 404 / 模型不存在 | 模型名写错了。点「获取可用模型」从服务商拉真实列表，别手打 |
| 提示"向量维度不匹配" | 中途换过向量模型，旧索引已失效 → 删掉知识库重新上传 |
| 界面点了没反应、样式错乱 | 浏览器缓存了旧版前端，**按 Ctrl+F5 强刷** |
| 8000 端口被占用 | 换端口：`python run_demo.py --port 8080` |
| 改了后端 `.py` 却没生效 | uvicorn 未开热重载，**必须重启服务**（Ctrl+C 后重新运行） |
| 想看接口文档 | 打开 <http://127.0.0.1:8000/docs>（FastAPI 自动生成，可在线调试） |

想连 MySQL、接 Neo4j 图谱、或改前端源码，见文末[「完整模式」](#完整模式可选)。

---

## 核心功能

| 功能 | 说明 |
|---|---|
| **三路混合检索** | 向量检索（ChromaDB）+ 关键词检索 + 图谱检索（Neo4j）并行召回，融合排序后送入 LLM |
| **检索降级策略** | 任一路召回为空或不可用自动降级；Neo4j 未部署时静默跳过，不因单点故障中断问答 |
| **SSE 流式输出** | Server-Sent Events 逐字推送，首字响应更快，避免长答案的等待焦虑 |
| **答案溯源** | 每条回答附带来源文档、原文片段与相似度分数，可点击跳转原文 |
| **链路参数可配置** | top-k、相似度阈值、各路检索权重、融合策略等全部可通过配置页调整，无需改代码 |
| **文档解析** | 支持 PDF / Word / Excel / Markdown / TXT，自动分块与向量化入库 |
| **多知识库隔离** | 不同知识库独立存储与检索，支持文档级权限控制 |
| **权限与审计** | JWT 鉴权 + RBAC 四级角色（管理员 / 知识库管理员 / 普通用户 / 访客），关键操作写入审计日志 |
| **自带 Key（BYOK）** | 每个用户在个人设置里配置自己的 Key、服务地址与模型，互不干扰，也无需改服务端配置 |

---

## 技术栈

**后端**：Python 3.11 · FastAPI · SQLAlchemy · Uvicorn
**前端**：Vue 3 · Vite · Element Plus · Pinia · Vue Router · ECharts · markdown-it

**存储**（除向量库外全部可选）：

| 组件 | 用途 | 是否必需 |
|---|---|---|
| SQLite | 业务数据默认存储，开箱即用 | ✅ 默认 |
| MySQL | 业务数据，配置 `MYSQL_HOST` 后自动切换 | 可选 |
| ChromaDB | 向量库，嵌入式运行，无需启服务 | ✅ 默认 |
| Neo4j | 知识图谱检索，未部署时自动降级跳过 | 可选 |

**AI**：兼容 OpenAI 协议的任意服务商。默认预设阿里云百炼，实际使用哪个由使用者在界面上决定。

> 关于 Redis / Celery：早期规划里曾打算用于会话缓存与异步任务，目前代码中**没有任何引用**，配置项已移除，README 不再声称。技术选型以代码实际实现为准。

---

## 架构

```
用户提问
   │
   ▼
查询路由 ──┬──► 向量检索（ChromaDB）
           ├──► 关键词检索（关系库全文匹配）
           └──► 图谱检索（Neo4j，未部署则跳过）
   │
   ▼
融合排序（权重可配）→ 降级判断 → 上下文组装
   │
   ▼
LLM 生成 ──► SSE 流式推送 ──► 前端逐字渲染
   │
   ▼
答案溯源（来源文档 + 原文片段 + 相似度）
```

**目录结构**

```
backend/
  app/
    api/          # API 模块：auth / config / dashboard / documents /
                  #   graph / history / knowledge / qa / users / ai
    core/         # 配置加载、JWT 鉴权、依赖注入、AI 凭据解析、服务商预设
    db/           # 关系库 / ChromaDB / Neo4j 连接层与轻量迁移
    models/       # SQLAlchemy 模型
    schemas/      # Pydantic 请求/响应模型
    rag/          # RAG 引擎：parser / embedding / retriever /
                  #   graph_retriever / llm / engine
    utils/        # 通用工具
  tests/          # pytest 测试
  demo_docs/      # 示例文档，用于快速体验
  run_demo.py     # 一键启动
frontend/
  src/            # Vue 3 页面与组件
  dist/           # 构建产物（入库，便于免装 Node 直接运行）
.github/workflows/test.yml   # CI：Python 3.11 + pytest
```

---

## 测试

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -v
```

测试覆盖 API 接口、鉴权与权限、RAG 引擎各模块（embedding / retriever / graph_retriever / llm / engine）、文档解析与文本处理工具。

测试使用独立的 SQLite 库并在无外部服务的情况下运行（见 `tests/conftest.py`），因此对外部 API 的调用均通过 mock 隔离——**测试结果不依赖任何 API Key 或网络**。

---

## 完整模式（可选）

### 切换到 MySQL

在 `backend/.env` 中填写连接信息即可，其余行为完全一致：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=db_qa_core
```

不填 `MYSQL_HOST` 时使用内置 SQLite（`backend/data/app.db`）。

### 启用知识图谱检索

安装并启动 Neo4j 后，在 `.env` 中填写：

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=你的密码
```

也可以在界面上不需要做任何切换：系统会探测连通性，连不上就跳过图谱检索，问答照常工作。

### 改前端源码

```bash
cd frontend
npm install
npm run dev      # 开发模式，已配置 /api 代理到 8000 端口
npm run build    # 构建到 dist/，由后端直接托管
```

### 批量导入文档

```bash
cd backend
python batch_import.py     # 目录通过环境变量 KB1_DATA_DIR 指定
python build_graph.py      # 构建图谱（可选）
```

---

## 配置说明

运行时参数可在系统配置页在线调整，改完即时生效。环境变量参考 `.env.example`：

| 类别 | 关键配置 |
|---|---|
| 数据库 | `DATABASE_URL`、`MYSQL_*` |
| 图谱 | `NEO4J_*`、`NEO4J_ENABLED` |
| 鉴权 | `JWT_SECRET_KEY`、`JWT_ALGORITHM`、`JWT_EXPIRE_HOURS` |
| 大模型（系统兜底） | `LLM_MODEL`、`LLM_API_KEY`、`LLM_API_BASE` |
| 向量化（系统兜底） | `EMBEDDING_MODEL`、`EMBEDDING_API_KEY` |

> 上表中 AI 相关配置只是**系统兜底值**。使用者在个人设置里填的配置优先级更高，因此部署者无需为使用者准备 Key。

---

## 安全说明

- **默认账号仅供本地演示**：`run_demo.py` 会创建 `admin / admin123`。部署到任何可被他人访问的环境前，必须先修改密码。
- **JWT 密钥不再有默认值**：未配置 `JWT_SECRET_KEY` 时，服务每次启动随机生成并打印一条警告，避免出现「源码里写死的公开密钥 → 令牌可被伪造」。需要登录态跨重启保留、或多进程部署时，请显式配置该变量。
- **初始化接口默认关闭**：`POST /api/v1/auth/init` 无需登录即可调用，现默认返回 403，仅 `.env` 中设置 `ALLOW_INIT_ADMIN=true` 才启用，且不再明文回传口令。
- **密钥不进版本库**：`.env`、`*.db`、`chroma_data/` 已被 `.gitignore` 排除；使用者的 Key 只保存在其本人账号记录里，账号之间互不可见。

---

## 已知限制与后续改进

- **用户 API Key 明文存储在数据库中**：生产环境应改为加密存储（如 KMS 或数据库层加密），避免泄露风险。当前设计把 Key 归属到使用者本人，是为了让每个体验者用自己的额度，而不是共用部署者的。
- **`POST /api/auth/init` 为开发期初始化接口**：默认已关闭（返回 403），仅在 `.env` 设置 `ALLOW_INIT_ADMIN=true` 时启用，且不再明文回传默认口令。生产部署应通过环境变量注入初始密码，并限制该接口的调用来源。
- **测试环境用 SQLite 替代 MySQL**：SQLite 在类型约束、并发行为上与 MySQL 并不完全一致，因此测试通过不等于生产环境行为完全等价。
- **向量模型切换后需重建索引**：不同向量模型维度不同，换模型后旧向量无法比对，需要清空知识库重新上传文档（系统会在检索时给出维度不匹配的明确提示）。
- **前端构建产物 `dist/` 已入库**：构建产物通常不纳入版本管理，这里为了使克隆者免装 Node.js 而破例，属于有意识的取舍。

---

## 开发说明

本项目配套完整设计文档，位于仓库根目录：

- `需求说明书.md` —— 需求分析
- `开发计划.md` —— 迭代计划
- `概要设计说明书.docx` / `详细设计说明书.docx` —— 系统设计
- `数据库设计说明书.docx` —— 数据模型
- `启动指南.md` —— 本地环境搭建
