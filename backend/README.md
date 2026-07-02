<p align="center">
  <h1 align="center">🧠 LMind Agent</h1>
  <p align="center">
    <strong>本地优先 · 隐私安全 · 智能问答</strong>
  </p>
  <p align="center">
    一个基于 RAG（检索增强生成）的本地知识库智能问答系统，让你的文档"活"起来。
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.136+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs">
</p>

---

## 📖 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [安装](#安装)
- [配置](#配置)
- [数据迁移](#数据迁移)
- [API 文档](#api-文档)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

LMind Agent 是一个**本地优先**的智能知识库问答系统。它使用 RAG（Retrieval Augmented Generation）技术，将你的私有文档（PDF、Word、Markdown 等）转化为可对话的知识库，通过大语言模型（LLM）提供准确、有引用的智能问答。

### 为什么选择 LMind Agent？

| 特性 | 说明 |
|------|------|
| 🔒 **数据隐私** | 所有数据存储在本地，不上传至第三方 |
| 🎯 **精准回答** | 向量检索 + 全文检索 + 重排序，多路召回保障精度 |
| 📎 **来源引用** | 每个回答都附带引用来源，可追溯、可验证 |
| 🔌 **MCP 集成** | (功能未开发) 支持 Model Context Protocol，可扩展外部工具 |
| 🐳 **一键部署** | 支持 Docker Compose 一键启动全部服务 |
| ⚡ **流式输出** | 支持 SSE 流式回答，体验流畅 |
| 🧩 **多格式支持** | PDF、DOCX、Markdown、TXT 等多种文档格式 |

### 应用场景

- **个人知识管理** — 建立私人知识库，随时检索和问答
- **企业文档助手** — 内部文档智能检索，提升工作效率
- **学术研究** — 论文、文献资料的知识提取与问答
- **客服系统** — 基于产品文档的智能客服

---

## 核心特性

### 🔍 多路召回 RAG 引擎

- **向量检索（Dense）**：基于 embedding 的语义相似度检索
- **全文检索（Sparse）**：基于 BM25 的关键词检索
- **RRF 融合**：倒数排序融合算法，结合多路检索结果
- **重排序（Reranker）**：使用 HuggingFace 模型对召回结果精排
- **来源引用**：回答附带文档来源和相关性评分

### 📄 文档处理流水线

- 支持 PDF、DOCX、Markdown、TXT 等多种格式
- 智能文本分块，保留文档结构
- 异步任务队列处理，不阻塞主服务
- OCR 支持（通过 RapidOCR）

### 🤖 智能 Agent

- 知识库问答 Agent — 基于文档内容的精准回答
- 研究型 Agent — 深度分析文献资料 （未开发）
- 工具调用 — 支持联网搜索、知识库检索等工具（未开发）
- 多轮对话 — 保持上下文，支持追问和深入讨论（目前仅支持会话窗口近三轮对话上下文）

### 🔧 MCP 协议支持（未开发）

- 集成 Model Context Protocol，可接入外部 MCP 服务
- 支持 MCP 工具的动态注册与调用

### 📊 可观测性

- 集成 LangSmith 进行 LLM 调用链追踪
- 结构化日志（Loguru）
- 请求级别追踪（X-Request-Id）

---

## 系统架构

未实现的功能：
1、MCP Integration
2、redis cache 

```
┌─────────────────────────────────────────────────────────┐
│                     Client (Web / API)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  FastAPI Application                      │
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │ Auth     │ Knowledge│ Chat     │ MCP Integration  │  │
│  │ Module   │ Base     │ Module   │ Module           │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
└──────┬──────────────┬────────────────┬─────────────────┘
       │              │                │
┌──────▼──────┐ ┌─────▼─────┐ ┌───────▼────────┐
│  PostgreSQL │ │   Redis   │ │  File Storage  │
│  (pgvector) │ │ (Cache/Q) │ │  (Local / S3)  │
└─────────────┘ └───────────┘ └────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│              Worker Processes                │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │ doc_worker   │  │  evaluation_worker   │ │
│  │ (文档处理)    │  │  (测评评估)           │ │
│  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 问答流程

```
用户提问 → 查询优化 → 向量化 → 多路召回 → RRF融合 → 重排序 → LLM生成 → 流式返回
                                    │                        │
                              pgvector + BM25          附带来源引用
```

---

## 技术栈

| 类别 | 技术 |
|------|------|
| **Web 框架** | FastAPI + Uvicorn |
| **数据库** | PostgreSQL + pgvector（向量存储） |
| **缓存/队列** | Redis（缓存 + 消息队列） |
| **ORM** | SQLAlchemy 2.0（异步） |
| **数据迁移** | Alembic |
| **LLM 框架** | LangChain + LangGraph |
| **嵌入模型** | OpenAI / 兼容 API（sentence-transformers 本地可选） |
| **重排模型** | HuggingFace Transformers（BAAI/bge-reranker 系列） |
| **文档解析** | PyPDF2 / pdfplumber / python-docx / PyMuPDF / Unstructured |
| **OCR** | RapidOCR + ONNX Runtime |
| **分词** | jieba |
| **日志** | Loguru |
| **部署** | Docker + Docker Compose |

---

## 快速开始

本地启动
```python
# 启动服务
uv run main.py
# 启动文档处理 Worker（另一个终端）
uv run doc_worker.py
# 启动测评评估 Worker（另一个终端）
uv run evaluation_worker.py
```

docker 启动
```python
# 1. 复制.env.example为.env.docker，并修改配置

# 2.构建镜像
docker build -t app .

# 3.启动容器服务
docker compose up -d 
```

### 前置要求

- **Python** >= 3.11
- **PostgreSQL** 14+（需要 pgvector 扩展）
- **Redis** 6+
- **uv**（Python 包管理器，推荐）

### Docker 一键部署（推荐）

```bash
# 1. 克隆项目
git clone 
cd LMindAgent/backend

# 2. 配置环境变量
cp .env.example .env.docker
# 编辑 .env.docker，填入你的 API Key 等配置

# 3. 构建并启动
docker compose up -d

# 4. 查看日志
docker compose logs -f app

# 5. 访问 API 文档
# 浏览器打开 http://localhost:8000/docs
```

### 本地开发部署

```bash
# 1. 克隆项目
git clone 
cd LMindAgent/backend

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入数据库连接信息、API Key 等

# 4. 启动 PostgreSQL + Redis（使用 Docker 或本地服务）
docker compose up -d pgsql redis

# 5. 执行数据库迁移
uv run alembic upgrade head

# 6. 生成密钥
.env 配置密钥, jwt和aes
uv run -m scripts.generate_jwt
uv run -m scripts.generate_aes

# 7. 启动服务
uv run main.py

# 8. 启动文档处理 Worker（另一个终端）
uv run doc_worker.py
```

---

## 安装
```python
# 初始化项目
uv init
# 初始化虚拟环境
uv add -r requirements.txt
# 添加依赖
uv add package_name
# 同步依赖
uv sync 
# 导出生产环境的依赖，排除开发依赖和哈希值
uv export --no-dev --no-hashes --output-file requirements.txt
```

---

## 配置
### 数据库配置
```python
# 1.配置redis
本地配置或者用desktop 配置redis镜像

# 2.配置pgvector
通过docker desktop方式安装pgvector(推荐)

创建数据库 local_mind_agent_db
执行 sql 安装插件
CREATE EXTENSION if not exists vector;
```
### 其他配置
```python
# 1.复制.env.example为.env，并修改配置

# 2.配置密钥, jwt和aes
# 密钥自己填写
# jwt
uv run -m scripts.generate_jwt
# aes
uv run -m scripts.generate_aes

# 3.配置嵌入模型embedding API和key

# 4.配置重排模型，只支持huggingface中支持的模型
https://huggingface.co/spaces/mteb/leaderboard

# 5.配置langsmith API和key
https://smith.langchain.com/
```

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `environment` | 运行环境：development / test / production | `development` |
| `database_url` | PostgreSQL 连接地址 | `postgresql+asyncpg://...` |
| `redis_url` | Redis 连接地址 | `redis://127.0.0.1:63796/0` |
| `jwt_secret` | JWT 签名密钥 | 需要自行生成 |
| `aes_key_hex` | AES 加密密钥 | 需要自行生成 |
| `openai_api_key` | OpenAI API Key（或兼容接口） | 需要填写 |
| `openai_api_base` | OpenAI API 地址（支持中转站） | `https://api.openai.com/v1` |
| `embedding_vector_model` | 嵌入模型名称 | `text-embedding-3-small` |
| `RERANKER_MODEL_NAME` | 重排模型（HuggingFace） | `BAAI/bge-base-en-v1.5` |
| `RERANKER_TOP_K` | 重排后保留数量 | `5` |
| `storage_backend` | 文件存储后端：local | `local` |
| `max_upload_mb` | 最大上传文件大小（MB） | `200` |
| `LANGSMITH_TRACING` | 是否启用 LangSmith 追踪 | `false` |

---

## 数据迁移
```python 
# 初始化迁移目录
# 同步方式
alembic init alembic
# 异步方式(本项目使用)
alembic init -t async alembic
# 创建迁移脚本
alembic revision --autogenerate -m "init"
# 更新数据库
alembic upgrade head
# 回滚到指定版本
alembic downgrade <version>
# 查看迁移历史
alembic history
# 查看当前版本
alembic current
```
修改迁移的配置
```python
# 需要配置 alembic/env.py
# 直接复制到run_migrations_offline函数上方即可

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入你的模型
from app.db.base import Base
from app.models import init_model  # 导入所有模型
init_model()

# 导入你的配置
from app.core.config import get_settings
settings = get_settings()

config = context.config

# 从配置获取数据库URL
config.set_main_option('sqlalchemy.url', settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
```

---

## API 文档

启动服务后，访问以下地址查看完整的 Swagger API 文档：

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 核心 API 模块

| 模块 | 说明 |
|------|------|
| `/api/v1/auth` | 用户认证（注册/登录/Token 刷新） |
| `/api/v1/users` | 用户管理 |
| `/api/v1/knowledge_bases` | 知识库 CRUD |
| `/api/v1/documents` | 文档上传与管理 |
| `/api/v1/chat` | 知识库问答（支持 SSE 流式） |
| `/api/v1/notes` | 笔记管理 |
| `/api/v1/tasks` | 任务管理 |
| `/api/v1/mcp` | MCP 服务集成 |
| `/api/v1/model_configs` | 模型配置管理 |
| `/api/v1/evaluation` | 问答测评 |
| `/api/v1/files` | 文件管理 |

---

## 项目结构

```
backend/
├── main.py                     # 应用入口
├── doc_worker.py               # 文档处理 Worker
├── evaluation_worker.py        # 测评 Worker
├── pyproject.toml              # 项目依赖配置
├── Dockerfile                  # Docker 镜像构建
├── docker-compose.yml          # Docker 编排
├── .env.example                # 环境变量模板
│
├── app/
│   ├── __init__.py             # FastAPI 应用工厂
│   ├── api/
│   │   ├── routes.py           # 路由注册中心
│   │   └── v1/                 # API v1 端点
│   │       ├── auth.py         # 认证接口
│   │       ├── users.py        # 用户接口
│   │       ├── knowledge_bases.py  # 知识库接口
│   │       ├── documents.py    # 文档接口
│   │       ├── chat.py         # 问答接口
│   │       ├── notes.py        # 笔记接口
│   │       ├── tasks.py        # 任务接口
│   │       ├── mcp.py          # MCP 接口
│   │       ├── model_configs.py # 模型配置接口
│   │       ├── evaluation.py   # 测评接口
│   │       ├── files.py        # 文件接口
│   │       └── home.py         # 首页接口
│   │
│   ├── agents/                 # AI Agent 模块
│   │   ├── agent.py            # Agent 入口
│   │   ├── prompts/            # Prompt 模板
│   │   ├── tools/              # Agent 工具
│   │   │   ├── knowledge_base.py   # 知识库检索工具
│   │   │   ├── web_search.py       # 联网搜索工具
│   │   │   ├── call_mcp_tool.py    # MCP 工具调用
│   │   │   └── weather.py          # 天气查询工具
│   │   ├── workflows/          # Agent 工作流
│   │   │   ├── qa_workflow.py      # 问答工作流
│   │   │   └── research_workflow.py # 研究工作流
│   │   └── history/            # 对话历史管理
│   │
│   ├── rag/                    # RAG 检索增强生成
│   │   ├── retriever.py        # 向量检索 + 全文检索 + RRF 融合
│   │   ├── re_ranker.py        # 重排序
│   │   ├── loader.py           # 文档加载
│   │   ├── splitter.py         # 文本分块
│   │   ├── citation.py         # 引用生成
│   │   ├── clean_text.py       # 文本清洗
│   │   └── embeddings.py       # 嵌入模型管理
│   │
│   ├── models/                 # ORM 模型
│   │   ├── user.py
│   │   ├── knowledge_base.py
│   │   ├── document.py
│   │   ├── document_chunk.py
│   │   ├── message.py
│   │   ├── note.py
│   │   ├── task.py
│   │   ├── mcp.py
│   │   └── model_config.py
│   │
│   ├── schemas/                # Pydantic 数据校验
│   ├── services/               # 业务逻辑层
│   ├── db/                     # 数据库层
│   │   ├── base.py             # SQLAlchemy Base
│   │   ├── session.py          # 会话管理
│   │   ├── repositories/       # 数据仓库层
│   │   └── redis_db/           # Redis 工具
│   │       ├── cache.py        # 缓存
│   │       ├── queue.py        # 消息队列
│   │       ├── lock.py         # 分布式锁
│   │       └── pubsub.py       # 发布订阅
│   │
│   ├── integrations/           # 外部集成
│   │   ├── llm_provider.py     # LLM 提供商抽象
│   │   ├── model_config_provider.py
│   │   ├── mcp_client.py       # MCP 客户端
│   │   └── mcp_registry.py     # MCP 注册中心
│   │
│   ├── storage/                # 文件存储
│   │   ├── local_storage.py    # 本地存储
│   │   ├── file_storage.py     # 文件存储抽象
│   │   └── object_storage.py   # 对象存储（S3 兼容）
│   │
│   ├── workers/                # 后台 Worker
│   │   ├── document_consumer.py    # 文档处理消费者
│   │   ├── evaluation_consumer.py  # 测评消费者
│   │   └── summary_consumer.py     # 摘要消费者
│   │
│   ├── middleware/             # 中间件
│   │   ├── request_id.py       # 请求 ID
│   │   └── access_log.py       # 访问日志
│   │
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── log.py              # 日志配置
│   │   ├── errors.py           # 异常处理
│   │   └── events.py           # 事件管理
│   │
│   ├── utils/                  # 工具函数
│   │   ├── generate_id.py      # ID 生成
│   │   ├── time_.py            # 时间工具
│   │   └── format_number.py    # 数字格式化
│   │
│   └── tests/                  # 测试
│
└── scripts/                    # 工具脚本
    ├── generate_jwt.py         # JWT 密钥生成
    └── generate_aes.py         # AES 密钥生成
```

---

## 开发指南

### Worker 服务说明

项目包含三个独立的 Worker 进程，通过 Redis Stream 消费任务：

| Worker | 文件 | 说明 |
|--------|------|------|
| **doc_worker** | `doc_worker.py` | 异步处理文档解析、分块、向量化 |
| **evaluation_worker** | `evaluation_worker.py` | 处理问答测评任务 |

### 添加新的文档格式支持

1. 在 `app/rag/loader.py` 中添加新的文档加载器
2. 注册到文档加载器工厂
3. 在 `allowed_upload_mime_types` 中添加对应的 MIME 类型

### 自定义 Prompt

编辑 `app/agents/prompts/prompt.py` 中的 Prompt 模板，可以自定义：
- 系统提示词
- 文档上下文格式
- 对话历史格式
---


## 待开发和优化
- [ 1 ] 优化 RAG 文档处理(分片规则和策略, 增加父子文档或者pdf to markdown 按标题切分)
- [ 2 ] 优化对话记忆, 历史记录和上下文的功能
- [ 3 ] 优化文档检索功能
- [ 4 ] 增加 MCP 功能
- [ 5 ] 增加tools工具的调用



## 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

