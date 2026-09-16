# 智能问答系统（RAG）

基于检索增强生成（RAG）的企业知识库问答系统。支持文档上传与解析、**三路混合检索**、SSE 流式输出、**答案级溯源**，并提供多知识库管理、检索链路参数全量可配置与操作审计能力。

> 面向的场景：企业内部制度、财政数据集等文档的问答查询——用户提问后，系统不仅给出答案，还会**标注每段回答来自哪份文档的哪一段原文**，解决大模型"胡说"无法核验的问题。

<!-- CI 徽章：Actions 跑绿后取消注释 -->
<!-- ![Tests](https://github.com/TangGuojian/rag-qa-system/actions/workflows/test.yml/badge.svg) -->

---

## 核心功能

| 功能 | 说明 |
|---|---|
| **三路混合检索** | 向量检索（ChromaDB）+ 关键词检索 + 图谱检索（Neo4j）并行召回，融合排序后送入 LLM |
| **检索降级策略** | 任一路召回为空或超时自动降级，保证服务可用性，不因单点故障中断问答 |
| **SSE 流式输出** | Server-Sent Events 逐字推送，首字响应更快，避免长答案的等待焦虑 |
| **答案溯源** | 每条回答附带来源文档、原文片段与相似度分数，可点击跳转原文 |
| **链路参数可配置** | top-k、相似度阈值、各路检索权重、融合策略等全部可通过配置页调整，无需改代码 |
| **文档解析** | 支持 PDF / Word / Excel / TXT，自动分块与向量化入库 |
| **多知识库隔离** | 不同知识库独立存储与检索，支持文档级权限控制 |
| **权限与审计** | JWT 鉴权 + RBAC 四级角色（管理员 / 知识库管理员 / 普通用户 / 访客），关键操作写入审计日志 |

---

## 技术栈

**后端**：Python 3.11 · FastAPI · SQLAlchemy · Uvicorn
**前端**：Vue 3 · Vite · Element Plus · Pinia · Vue Router · ECharts · markdown-it
**存储**：
- MySQL —— 业务数据（用户、知识库、文档元数据、会话历史、审计日志）
- ChromaDB —— 向量库（文档分块 embedding）
- Neo4j —— 图谱库（实体与关系，支撑图谱检索）
- Redis —— 会话缓存与 Celery 任务队列

**AI**：DashScope 兼容接口（`qwen3.7-plus` 生成 + `text-embedding-v3` 向量化），API Key 支持用户级配置

---

## 架构

```
用户提问
   │
   ▼
查询路由 ──┬──► 向量检索（ChromaDB）
           ├──► 关键词检索（MySQL）
           └──► 图谱检索（Neo4j）
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
    api/          # 9 个 API 模块：auth / config / dashboard / documents /
                  #   graph / history / knowledge / qa / users
    core/         # 配置加载、JWT 鉴权、依赖注入
    db/           # MySQL / ChromaDB / Neo4j 连接层
    models/       # 7 个 SQLAlchemy 模型
    schemas/      # Pydantic 请求/响应模型
    rag/          # RAG 引擎：parser / embedding / retriever /
                  #   graph_retriever / llm / engine
    utils/        # 通用工具
  tests/          # 17 个 pytest 测试文件
frontend/
  src/            # Vue 3 页面与组件
.github/workflows/test.yml   # CI：Python 3.11 + pytest
```

---

## 快速开始

### 1. 准备依赖服务

本地需先启动 MySQL、Neo4j、Redis（ChromaDB 以嵌入式模式运行，无需单独启动）。

### 2. 后端

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt

# 复制配置模板并填写自己的连接信息与 API Key
cp .env.example .env

uvicorn app.main:app --reload
```

后端默认运行在 `http://127.0.0.1:8000`，接口文档见 `http://127.0.0.1:8000/docs`。

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 导入知识库文档

```bash
cd backend
python batch_import.py     # 目录通过环境变量 KB1_DATA_DIR 指定
python build_graph.py      # 构建图谱（可选）
```

---

## 测试

```bash
cd backend
pytest -v
```

测试覆盖 API 接口、鉴权与权限、RAG 引擎各模块（embedding / retriever / graph_retriever / llm / engine）、文档解析与文本处理工具。

---

## 配置说明

所有可调参数集中在 `backend/.env`（参考 `.env.example`）：

| 类别 | 关键配置 |
|---|---|
| 数据库 | `MYSQL_*`、`NEO4J_*`、`CHROMADB_*`、`REDIS_*` |
| 鉴权 | `JWT_SECRET_KEY`、`JWT_ALGORITHM`、`JWT_EXPIRE_HOURS` |
| 大模型 | `LLM_MODEL`、`LLM_API_KEY`、`LLM_API_BASE` |
| 向量化 | `EMBEDDING_MODEL`、`EMBEDDING_API_KEY` |

> 检索链路的运行时参数（top-k、阈值、权重等）可在系统配置页在线调整，改完即时生效。

---

## 已知限制与后续改进

- **API Key 目前明文存储在 MySQL**：生产环境应改为加密存储，或统一使用服务端密钥池，避免用户密钥泄露风险。
- **`POST /api/auth/init` 为开发期初始化接口**：可无鉴权创建管理员账号。生产部署应通过环境变量注入初始密码，并限制该接口的调用来源。
- **CI 中的外部依赖**：部分测试依赖 MySQL / Neo4j / LLM API，CI 环境未提供这些服务时会被跳过或失败。

---

## 开发说明

本项目配套完整设计文档，位于仓库根目录：

- `需求说明书.md` —— 需求分析
- `开发计划.md` —— 迭代计划
- `概要设计说明书.docx` / `详细设计说明书.docx` —— 系统设计
- `数据库设计说明书.docx` —— 数据模型
- `启动指南.md` —— 本地环境搭建
