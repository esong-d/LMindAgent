# 个人知识库 Agent 后端架构设计

技术栈：

```text
FastAPI + LangChain + PostgreSQL + pgvector
```

任务队列建议：

```text
MVP：FastAPI BackgroundTasks
正式版：Celery / RQ / Dramatiq + Redis
```

## 1. 后端目标

后端需要支撑：

- 知识库管理
- 文档上传、解析、切分、向量化
- RAG 检索问答
- Agent 工具调用
- 对话和笔记持久化
- 来源引用和检索过程记录
- 长任务进度跟踪
- 用户数据隔离

后端设计重点是稳定、可观测、可替换，而不是把所有逻辑都交给 LangChain。

## 2. 总体架构

```text
React Frontend
      ↓ HTTP / SSE
FastAPI API Layer
      ↓
Service Layer
      ↓
Agent / RAG Layer
      ↓
Repository / Storage Layer
      ↓
PostgreSQL + pgvector / File Storage / Redis / Model Providers
```

分层职责：

| 层 | 职责 |
| --- | --- |
| API Layer | 路由、鉴权、参数校验、响应格式 |
| Service Layer | 业务编排、事务、权限检查 |
| Agent Layer | Agent 工作流、工具调用、Prompt |
| RAG Layer | 文档加载、切分、Embedding、检索、rerank |
| Repository Layer | 数据库读写 |
| Infrastructure | 文件存储、任务队列、模型调用、日志 |

## 3. 实际目录结构

> 已实现。与设计版的主要差异：入口文件在项目根目录；API 路由增加了 v1 版本号；新增 middleware、utils、redis_db、evaluation 等模块。

```text
main.py                         ← 入口文件
doc_worker.py                   ← 文档处理独立 Worker
evaluation_worker.py            ← 评测独立 Worker
pyproject.toml
requirements.txt
Dockerfile
docker-compose.yml
alembic.ini
alembic/
  env.py
  versions/

scripts/
  generate_aes.py
  generate_jwt.py

app/
  api/
    deps.py
    routes.py
    v1/                         ← 版本化路由
      auth.py
      users.py
      knowledge_bases.py
      documents.py
      chat.py
      notes.py
      tasks.py
      mcp.py
      model_configs.py
      files.py
      home.py
      evaluation.py             ← 新增：评测模块

  core/
    config.py
    security.py
    log.py
    log_instance.py
    errors.py
    events.py

  middleware/                    ← 新增
    access_log.py
    request_id.py

  models/
    base.py
    user.py
    knowledge_base.py
    document.py
    document_chunk.py
    conversation.py
    message.py
    message_tools.py
    note.py
    task.py
    mcp.py
    model_config.py
    evaluation.py               ← 新增：评测相关模型

  schemas/
    user.py
    knowledge_base.py
    document.py
    chat.py
    note.py
    task.py
    mcp.py
    model_config.py
    evaluation.py               ← 新增：评测 Schema

  services/
    knowledge_base_service.py
    document_service.py
    ingestion_service.py
    retrieval_service.py
    chat_service.py
    note_service.py
    task_service.py
    mcp_service.py
    mcp_tool_service.py
    model_config_service.py
    file_service.py             ← 新增
    home_service.py             ← 新增
    evaluation_service.py       ← 新增

  agents/
    agent.py
    history/                    ← 新增：对话历史管理
      build.py
      cache.py
      search.py
    memory/                     ← 新增：Agent 记忆
    prompts/
      prompt.py
      query_prompt.py
      evaluation_prompt.py      ← 新增：评测 Prompt
    workflows/
      qa_workflow.py
      qa_graph_workflow.py      ← 新增：LangGraph 版 QA
      summarize_workflow.py
      research_workflow.py
    tools/
      call_mcp_tool.py
      knowledge_base.py
      weather.py                ← 新增：示例工具
      web_search.py             ← 新增：联网搜索

  rag/
    _query.py
    citation.py
    clean_text.py
    embeddings.py
    loader.py
    re_ranker.py
    retriever.py
    splitter.py

  db/
    session.py
    base.py
    redis_db/                   ← 新增：Redis 基础设施
      base.py
      cache.py
      client.py
      lock.py
      pubsub.py
      queue.py
      serializer.py
    repositories/
      _base.py                  ← 通用 Repository 基类
      user_repository.py
      knowledge_base_repository.py
      document_repository.py
      chunk_repository.py
      conversation_repository.py
      message_repository.py
      note_repository.py
      task_repository.py
      mcp_repository.py
      model_config_repository.py
      evaluation_group_repository.py   ← 新增
      evaluation_question_repository.py
      evaluation_run_repository.py
      evaluation_task_repository.py

  workers/                      ← 基于消息队列的 Consumer 模式
    document_consumer.py
    summary_consumer.py
    evaluation_consumer.py      ← 新增
    handlers/
      document_handle.py
      evaluation_handle.py

  storage/
    file_storage.py
    local_storage.py
    object_storage.py

  integrations/
    llm_provider.py
    embedding_provider.py
    model_config_provider.py
    mcp_client.py
    mcp_registry.py

  utils/                        ← 新增
    format_number.py
    generate_id.py
    time_.py

  tests/
    embeddings_test.py
    generate_secret_key.py
    load_split_test.py
    reranker_test.py
    stream_res_data.py
    test_aes.py
    test_import.py
    test_redis.py
```

## 4. 核心模块职责

### KnowledgeBaseService

负责：

```text
创建知识库
更新知识库设置
获取知识库列表
校验用户访问权限
```

### DocumentService

负责：

```text
上传文档
保存文件元数据
查看文档状态
删除文档
触发重新解析
```

### IngestionService

负责：

```text
加载文档
提取文本
清洗文本
切分 chunk
生成 embedding
写入 document_chunks
更新任务状态
```

### RetrievalService

负责：

```text
query rewrite
向量检索
关键词检索
rerank
返回可引用 chunks
```

### ChatService

负责：

```text
创建或继续会话
调用 Agent Workflow
流式输出回答
保存 messages
保存 sources 和 tool calls
```

### NoteService

负责：

```text
创建笔记
更新笔记
关联来源
从回答保存笔记
```

### TaskService

负责：

```text
创建任务
更新进度
记录错误
提供 SSE 任务事件
```

### ModelConfigService

负责：

```text
保存用户模型配置
加密存储 API Key
读取当前知识库使用的模型配置
测试模型连接
校验数据发送策略
为 Chat / Embedding 流程提供 Provider 实例
```

### McpService

负责：

```text
保存 MCP Server 配置
加密存储 MCP 环境变量中的敏感值
启动 / 停止 / 测试 MCP Server
发现 tools / resources / prompts
管理知识库可用 MCP Server
维护 MCP Server 状态
```

### McpToolService

负责：

```text
把 MCP tools 暴露为 Agent 可调用工具
执行 MCP 工具调用
校验工具权限策略
处理需要用户确认的调用
记录 MCP 调用日志
将 MCP 调用过程通过 SSE 返回前端
```

### FileService ← 新增：实际已实现

负责：

```text
文件上传校验（类型、大小）
本地文件存储
文件元数据管理
```

### HomeService ← 新增：实际已实现

负责：

```text
仪表盘总览数据聚合
文档/分片/笔记统计数据
最近活动记录
```

### EvaluationService ← 新增：实际已实现

负责：

```text
测评分组管理
测评问题 CRUD
测评任务创建与管理
测评运行与结果记录
对比回答与标准答案
```

## 5. 数据库设计

推荐使用：

```text
PostgreSQL + pgvector
```

### users

```text
id
email
name
password_hash
created_at
updated_at
```

### knowledge_bases

```text
id
user_id
name
description
settings_json
created_at
updated_at
```

### documents

```text
id
knowledge_base_id
user_id
filename
original_filename
file_type
file_size
storage_path
status
error_message
metadata_json
created_at
updated_at
```

文档状态：

```text
pending
parsing
chunking
embedding
ready
failed
deleted
```

### document_chunks

```text
id
document_id
knowledge_base_id
user_id
chunk_index
content
content_hash
token_count
page_number
section_title
metadata_json
embedding vector
created_at
```

建议索引：

```text
knowledge_base_id
document_id
content_hash
embedding vector index
```

### conversations

```text
id
knowledge_base_id
user_id
title
created_at
updated_at
```

### messages

```text
id
conversation_id
user_id
role
content
sources_json
tool_calls_json
metadata_json
created_at
```

### notes

```text
id
knowledge_base_id
user_id
title
content
source_type
source_id
source_refs_json
tags_json
created_at
updated_at
```

### tasks

```text
id
user_id
knowledge_base_id
document_id
type
status
progress
input_json
output_json
error_message
created_at
updated_at
```

任务状态：

```text
queued
running
succeeded
failed
canceled
```

### model_configs

用于保存用户自定义模型配置。

```text
id
user_id
name
provider
mode
base_url
api_key_encrypted
chat_model
embedding_model
data_policy
is_default
status
last_tested_at
last_test_result_json
created_at
updated_at
```

字段说明：

```text
provider: openai / azure_openai / openai_compatible / ollama / lm_studio / localai / vllm
mode: cloud / local / private
data_policy: chunks_only / summaries_allowed / local_only
status: untested / available / failed
```

### knowledge_base_model_settings

用于让不同知识库使用不同模型配置。

```text
id
knowledge_base_id
user_id
chat_model_config_id
embedding_model_config_id
created_at
updated_at
```

如果没有知识库级配置，则使用用户默认模型配置。

### mcp_servers

用于保存用户配置的 MCP Server。

```text
id
user_id
name
description
transport
command
args_json
url
env_json_encrypted
scope
status
is_enabled
last_connected_at
last_error
created_at
updated_at
```

字段说明：

```text
transport: stdio / http / sse
scope: global / knowledge_base / conversation
status: untested / connected / failed / disabled
```

### mcp_server_bindings

用于将 MCP Server 绑定到知识库或会话。

```text
id
user_id
mcp_server_id
knowledge_base_id
conversation_id
is_enabled
created_at
updated_at
```

### mcp_tools

缓存 MCP Server 暴露的工具清单。

```text
id
user_id
mcp_server_id
name
description
input_schema_json
permission_policy
is_enabled
last_synced_at
created_at
updated_at
```

权限策略：

```text
auto_allow_readonly
confirm_on_write
always_confirm
disabled
```

### mcp_resources

缓存 MCP Server 暴露的资源清单。

```text
id
user_id
mcp_server_id
uri
name
description
mime_type
metadata_json
last_synced_at
created_at
updated_at
```

### mcp_call_logs

记录 Agent 调用 MCP 工具的历史。

```text
id
user_id
conversation_id
message_id
mcp_server_id
mcp_tool_id
tool_name
status
arguments_json
result_summary
error_message
requires_approval
approved_by_user
created_at
completed_at
```

## 6. 文档处理流程

```text
1. 用户上传文件
2. API 校验文件类型和大小
3. FileStorage 保存原始文件
4. documents 创建记录，状态为 pending
5. TaskService 创建 document_parse 任务
6. Worker（Redis Stream Consumer）开始处理
7. Loader 提取文本
8. Splitter 切分 chunk
9. EmbeddingProvider 生成向量
10. ChunkRepository 批量写入
11. documents 状态更新为 ready
12. 前端通过任务事件看到进度
```

失败处理：

```text
解析失败：document.status = failed
Embedding 失败：允许重试
部分 chunk 失败：记录错误并回滚或标记失败
重复上传：通过 content_hash 检测
```

## 7. RAG 流程

基础问答流程：

```text
1. 接收用户问题
2. 读取会话上下文
3. 判断检索范围
4. query rewrite
5. 向量检索 top_k
6. 可选关键词检索
7. 可选 rerank
8. 构造 prompt
9. 调用 LLM
10. 生成回答
11. 生成 sources
12. 保存 message
13. 流式返回前端
```

第一版建议：

```text
Vector Search + 严格引用
```

第二阶段再加：

```text
Hybrid Search + Rerank
```

## 8. Agent Workflow 设计

不建议第一版使用完全开放式 ReAct Agent。

推荐使用受控工作流：

```text
QA Workflow
Summarize Workflow
Research Workflow
```

### QA Workflow

```text
理解问题
检索知识库
阅读 chunks
生成回答
生成引用
保存消息
```

### Summarize Workflow

```text
读取文档 chunks
分段摘要
合并摘要
生成关键点
可保存为笔记
```

### Research Workflow

```text
拆解子问题
分别检索
整合结论
输出结构化报告
附来源
```

## 9. Agent 工具

第一版工具建议：

```text
search_knowledge_base(query, kb_ids, top_k)
read_document_chunk(chunk_ids)
summarize_document(document_id)
create_note(title, content, source_refs)
call_mcp_tool(server_id, tool_name, arguments)
```

工具权限：

| 工具 | 是否需要确认 |
| --- | --- |
| search_knowledge_base | 否 |
| read_document_chunk | 否 |
| summarize_document | 否 |
| create_note | 可默认允许 |
| call_mcp_tool | 按 MCP 工具策略决定 |
| update_note | 建议确认 |
| delete_document | 不给 Agent |
| delete_knowledge_base | 不给 Agent |

### MCP 工具桥接

MCP tools 不建议直接全部暴露给 Agent。后端应先经过工具注册和权限过滤。

流程：

```text
1. ChatService 获取当前知识库可用 MCP Server
2. McpService 同步 tools / resources / prompts
3. McpToolService 根据权限策略筛选可用 tools
4. Agent Workflow 将允许的 MCP tools 注入工具列表
5. Agent 请求调用 MCP tool
6. McpToolService 判断是否需要用户确认
7. 执行 MCP tool 或等待前端确认
8. 记录 mcp_call_logs
9. 通过 SSE 返回工具调用状态
```

## 10. MCP 能力设计

### 10.1 支持范围

MCP 用于连接外部工具和数据源，例如：

```text
本地文件系统
浏览器自动化
GitHub
Notion
数据库
企业内部系统
自定义脚本工具
```

第一版建议优先支持：

```text
stdio MCP Server
OpenAI Agent 可控工具调用
工具清单展示
连接测试
权限确认
调用日志
```

第二阶段再扩展：

```text
HTTP / SSE MCP Server
Resources 读取
Prompts 管理
Server Marketplace
团队级 MCP 配置
```

### 10.2 MCP 连接生命周期

```text
1. 用户创建 MCP Server 配置
2. 后端保存配置并加密敏感环境变量
3. 用户点击测试连接
4. 后端启动或连接 MCP Server
5. 拉取 tools / resources / prompts
6. 写入 mcp_tools / mcp_resources
7. 用户选择启用范围和权限策略
8. Agent Workflow 按需使用
```

### 10.3 MCP 权限策略

```text
auto_allow_readonly: 只读工具自动执行
confirm_on_write: 可能写入的工具需要确认
always_confirm: 每次调用都确认
disabled: 禁用
```

后端必须强制执行权限策略，不能只依赖前端展示。

### 10.4 MCP 用户确认流程

当工具需要确认时：

```text
1. Agent 生成工具调用意图
2. 后端创建 pending mcp_call_log
3. SSE 推送 approval_required
4. 前端展示确认弹窗
5. 用户允许或拒绝
6. 前端调用 approval API
7. 后端继续执行或取消工具调用
8. SSE 推送执行结果
```

### 10.5 MCP 与隐私策略

MCP Server 可能访问本地文件、外部系统或私有数据，因此需要：

```text
按用户隔离 MCP Server
敏感环境变量加密
工具参数和返回结果可脱敏记录
默认禁用高风险工具
跨知识库调用前检查绑定关系
本地文件类 MCP 需要明确路径范围
```

## 11. API 设计

### Knowledge Bases

```text
POST /api/knowledge-bases
GET  /api/knowledge-bases
GET  /api/knowledge-bases/{id}
PATCH /api/knowledge-bases/{id}
DELETE /api/knowledge-bases/{id}
```

### Documents

```text
POST /api/documents/upload
GET  /api/knowledge-bases/{kb_id}/documents
GET  /api/documents/{id}
DELETE /api/documents/{id}
POST /api/documents/{id}/reprocess
POST /api/documents/{id}/summarize
```

### Chat

```text
POST /api/chat
POST /api/chat/stream
GET  /api/conversations
GET  /api/conversations/{id}
GET  /api/conversations/{id}/messages
DELETE /api/conversations/{id}
```

### Notes

```text
POST /api/notes
GET  /api/knowledge-bases/{kb_id}/notes
GET  /api/notes/{id}
PATCH /api/notes/{id}
DELETE /api/notes/{id}
```

### Tasks

```text
GET /api/tasks/{id}
GET /api/tasks/{id}/events
POST /api/tasks/{id}/cancel
```

### MCP

```text
POST   /api/mcp/servers
GET    /api/mcp/servers
GET    /api/mcp/servers/{id}
PATCH  /api/mcp/servers/{id}
DELETE /api/mcp/servers/{id}
POST   /api/mcp/servers/{id}/test
POST   /api/mcp/servers/{id}/sync
GET    /api/mcp/servers/{id}/tools
GET    /api/mcp/servers/{id}/resources
PATCH  /api/mcp/tools/{id}/permission
GET    /api/mcp/call-logs
POST   /api/mcp/call-logs/{id}/approve
POST   /api/mcp/call-logs/{id}/reject
```

知识库绑定：

```text
GET   /api/knowledge-bases/{kb_id}/mcp-servers
PATCH /api/knowledge-bases/{kb_id}/mcp-servers
```

## 12. SSE 事件设计

Chat 流式事件：

```text
message_start
step_updated
tool_started
tool_finished
source_added
mcp_approval_required
mcp_tool_started
mcp_tool_finished
message_delta
message_done
error
```

任务事件：

```text
task_started
task_progress
task_log
task_done
task_failed
```

Chat event 示例：

```json
{
  "event": "source_added",
  "data": {
    "document_id": "doc_1",
    "chunk_id": "chunk_12",
    "filename": "RAG 产品调研.pdf",
    "page_number": 12,
    "score": 0.91
  }
}
```

## 13. 模型配置与 Provider 设计

建议抽象：

```text
LLMProvider
EmbeddingProvider
ModelConfigService
```

不要让业务代码直接依赖某一个模型 SDK。

接口概念：

```text
LLMProvider.chat(messages, stream=False)
LLMProvider.stream_chat(messages)
EmbeddingProvider.embed_documents(texts)
EmbeddingProvider.embed_query(text)
```

好处：

- 方便切换 OpenAI / Azure / 本地模型
- 方便做测试 mock
- 方便记录 token 和耗时

### 12.1 支持的模型模式

后端需要支持三类模型配置：

```text
cloud: 云模型 API
local: 本地模型
private: 私有部署模型
```

示例：

```text
cloud:
  OpenAI
  Azure OpenAI
  Anthropic compatible gateway

local:
  Ollama
  LM Studio
  LocalAI

private:
  vLLM OpenAI Compatible Server
  公司内网模型网关
  私有云模型服务
```

### 12.2 OpenAI Compatible 优先

建议后端优先支持 OpenAI Compatible API。

原因：

```text
OpenAI 官方 API
Ollama
LM Studio
vLLM
LocalAI
很多私有模型网关
```

都可以通过近似接口接入。

### 12.3 模型配置读取流程

Chat 请求时：

```text
1. 获取 user_id 和 knowledge_base_id
2. 查询 knowledge_base_model_settings
3. 如果知识库未单独配置，读取用户默认 model_configs
4. 解密 API Key
5. 根据 provider 创建 LLMProvider
6. 根据 data_policy 检查是否允许发送当前上下文
7. 执行 Chat / Agent Workflow
```

文档向量化时：

```text
1. 获取知识库 embedding_model_config_id
2. 如果未配置，读取用户默认 embedding 配置
3. 创建 EmbeddingProvider
4. 批量生成 embedding
5. 写入 document_chunks
```

### 12.4 API Key 加密

API Key 不能明文存储。

建议：

```text
使用应用级 encryption key 加密
数据库只存 api_key_encrypted
接口返回时只返回 masked key
支持清除和替换 key
日志永不记录明文 key
```

返回示例：

```json
{
  "id": "cfg_1",
  "provider": "openai_compatible",
  "base_url": "https://api.openai.com/v1",
  "chat_model": "gpt-4.1-mini",
  "api_key_masked": "sk-••••••••••••"
}
```

### 12.5 连接测试

后端提供连接测试接口：

```text
POST /api/model-configs/{id}/test
```

测试内容：

```text
base_url 是否可访问
API Key 是否有效
chat_model 是否可调用
embedding_model 是否可调用
响应延迟
错误信息
```

测试结果写入：

```text
model_configs.status
model_configs.last_tested_at
model_configs.last_test_result_json
```

### 12.6 数据发送策略

用户可以选择：

```text
chunks_only: 仅发送检索片段到模型
summaries_allowed: 允许发送完整文档摘要
local_only: 完全本地，不调用云模型
```

后端必须在 Chat / Summary / Research Workflow 前校验策略。

示例：

```text
如果 data_policy = local_only
且 provider.mode = cloud
则拒绝请求，并返回需要切换本地模型配置
```

这条策略应该在后端强制执行，不能只依赖前端。

### 12.7 模型配置 API

```text
POST   /api/model-configs
GET    /api/model-configs
GET    /api/model-configs/{id}
PATCH  /api/model-configs/{id}
DELETE /api/model-configs/{id}
POST   /api/model-configs/{id}/test
POST   /api/model-configs/{id}/set-default
```

知识库模型配置：

```text
GET   /api/knowledge-bases/{kb_id}/model-settings
PATCH /api/knowledge-bases/{kb_id}/model-settings
```

### 12.8 模型配置请求示例

```json
{
  "name": "我的本地 Ollama",
  "provider": "ollama",
  "mode": "local",
  "base_url": "http://localhost:11434/v1",
  "api_key": "",
  "chat_model": "qwen2.5:14b",
  "embedding_model": "nomic-embed-text",
  "data_policy": "local_only",
  "is_default": true
}
```

私有部署示例：

```json
{
  "name": "公司内网模型",
  "provider": "openai_compatible",
  "mode": "private",
  "base_url": "https://llm.internal.example.com/v1",
  "api_key": "internal-api-key",
  "chat_model": "qwen2.5-72b-instruct",
  "embedding_model": "bge-m3",
  "data_policy": "chunks_only"
}
```

## 14. 安全设计

用户隔离：

```text
所有查询必须带 user_id
所有知识库、文档、chunk、笔记、对话都绑定 user_id
Repository 层禁止跨用户读取
```

文件安全：

```text
限制文件类型
限制上传大小
保存文件时生成内部文件名
不直接暴露本地路径
解析失败不返回内部堆栈
```

Agent 安全：

```text
第一版不给删除类工具
修改已有内容需要确认
创建新笔记可以默认允许
回答必须基于来源或明确说明无法确认
```

模型配置安全：

```text
API Key 加密存储
API Key 不进入日志
接口不返回明文 API Key
连接测试错误信息需要脱敏
禁止普通用户读取其他用户的模型配置
local_only 策略由后端强制执行
```

MCP 安全：

```text
MCP Server 按 user_id 隔离
MCP 环境变量加密存储
MCP 工具权限由后端强制执行
写入和高风险工具需要用户确认
调用参数和结果日志需要支持脱敏
本地文件 MCP 需要限制可访问路径
禁用未绑定到当前知识库的 MCP Server
```

## 15. 可观测性

建议记录：

```text
request_id
user_id
conversation_id
message_id
query
rewritten_query
retrieved_chunk_ids
scores
selected_sources
model_name
input_tokens
output_tokens
latency_ms
error_message
```

模型调用还需要记录：

```text
model_config_id
provider
mode
base_url_host
chat_model
embedding_model
data_policy
connection_latency_ms
provider_error_code
```

MCP 调用还需要记录：

```text
mcp_server_id
mcp_tool_id
tool_name
permission_policy
requires_approval
approved_by_user
call_latency_ms
mcp_error_code
result_size
```

注意：

```text
不要记录 API Key
不要默认记录完整 prompt
敏感场景只记录 chunk ids 和 token 统计
```

前端展示简化版：

```text
检索了 8 个片段
引用了 3 个来源
生成耗时 6.2 秒
```

后端保留完整日志用于调试。

## 16. 测试策略

优先测试：

```text
文档上传校验
文档状态流转
chunk 切分
embedding 写入
权限隔离
检索结果格式
Chat sources 格式
笔记创建
任务失败处理
MCP Server 连接测试
MCP 工具权限策略
MCP 用户确认流程
```

测试层级：

```text
Unit Tests：splitter、retriever、service
Integration Tests：API + DB
Contract Tests：前后端响应格式
Smoke Tests：上传文档 -> 提问 -> 返回引用
```

## 17. 开发阶段

### 阶段 1：基础数据与文档导入 ✅

```text
用户/知识库 ✅
文档上传 ✅
文件存储 ✅
解析 ✅
切分 ✅
向量化 ✅
文档状态 ✅
```

### 阶段 2：RAG 问答 ✅

```text
检索 ✅
Prompt ✅
回答生成 ✅
来源引用 ✅
会话保存 ✅
```

### 阶段 3：Agent 工具 ✅

```text
总结文档 ✅
创建笔记 ✅
研究模式 ✅
Agent 步骤事件 ✅
MCP Server 配置 ✅
MCP 工具调用 ✅
MCP 权限确认 ✅
模型配置 ✅
评测系统 ✅
Redis 任务队列 ✅
```

### 阶段 4：可靠性（进行中）

```text
任务队列 ✅（Redis Stream）
失败重试
Hybrid Search
Rerank ✅
日志追踪 ✅
权限完善 ✅
```

## 18. 审核重点

建议重点审核：

```text
1. MVP 是否使用 BackgroundTasks，还是直接上 Celery
2. 是否确定 PostgreSQL + pgvector 作为统一存储
3. 第一版是否只做 Vector Search
4. Agent 是否采用受控 Workflow，而不是开放式 ReAct
5. 是否第一版就支持多用户
6. 文件存储用本地，还是对象存储
7. 是否需要本地模型兼容
8. 模型配置是用户级，还是知识库级也可覆盖
9. API Key 加密和连接测试是否第一版就做
10. local_only 数据策略是否作为后端强制规则
11. MCP 第一版支持 stdio 即可，还是需要 HTTP/SSE
12. MCP 工具调用默认策略是只读自动允许，还是全部确认
13. 本地文件类 MCP 是否需要路径白名单
14. MCP Server 配置是用户级，还是知识库级强绑定
```
