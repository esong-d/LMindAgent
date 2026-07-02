# 个人知识库 Agent 前端架构设计

技术栈实际使用：

```text
React + TypeScript + Vite + React Router + Ant Design
```

> 当前未使用 TanStack Query 或 Zustand，状态管理采用 localStorage + React Context + useReducer/useState 模式。

## 1. 前端目标

前端不是普通聊天界面，而是一个个人知识库工作台。

核心目标：

- 管理知识库、文档、笔记和对话
- 提供稳定的 Agent 对话入口
- 展示来源引用、检索结果和任务进度
- 支持文档上传、解析状态查看、失败重试
- 让用户清楚知道 Agent 当前基于什么上下文回答

## 2. 页面结构

> 已实现。当前路由为扁平结构，不使用 `kbId` 前缀；知识库切换通过全局状态管理。

```text
/                         总览（仪表盘）
/chat                     Agent 对话
/knowledge                知识库（RAG 可视化）
/documents                文档管理
/tasks                    任务列表
/tasks/:taskId            任务详情
/notes                    笔记
/evaluation               测评中心
  /evaluation/groups        测评分组
  /evaluation/questions     测评问题
  /evaluation/tasks         测评任务
  /evaluation/runs          测评记录
  /evaluation/results       测评结果
/settings                 设置（模型配置、MCP、用户偏好）
/login                    登录
/register                 注册
```

## 3. 布局架构

推荐三栏工作台：

```text
Topbar
├── 左侧 Sidebar：页面导航、知识库列表、用户信息
├── 中间 Main：当前页面主要内容
└── 右侧 Context Panel：来源、检索、步骤、记忆
```

底部保留全局 Agent 输入栏：

```text
Global Agent Composer
```

它在不同页面自动带入不同上下文：

| 页面 | 默认上下文 |
| --- | --- |
| 总览 | 当前知识库 |
| 对话 | 当前会话 |
| 文档管理 | 选中文档集合 |
| 文档详情 | 当前文档 |
| 笔记 | 当前笔记或笔记列表 |
| 设置 | 参数解释或配置辅助 |

## 4. 实际目录结构

> 已实现。与设计版的主要差异：无 `app/` 和 `components/ui/` 层，页面和功能模块更丰富；增加了登录注册、评测管理、知识图谱（总览）、系统设置等页面；使用 Ant Design 作为 UI 库。

```text
index.html
vite.config.ts
package.json
tsconfig.json
tsconfig.app.json
tsconfig.node.json
eslint.config.js

public/
  favicon.svg
  icons.svg
  logo.svg
  logo.png
  brain.svg

docs/
  images/                       ← 各页面截图

src/
  main.tsx                      ← 入口
  App.tsx
  index.css                     ← 全局基础样式

  context/                      ← React Context（替代 providers.tsx）
    AntdConfig.tsx              ← Ant Design 主题配置
    ThemeContext.tsx             ← 暗色/亮色主题切换

  components/                   ← 通用 UI 组件（无独立 ui/ 子目录）
    ThemeToggle/
    Toast/

  router/
    nav.tsx                     ← 导航配置
    router.tsx                  ← 路由定义

  layouts/                      ← 四栏工作台布局
    WorkspaceLayout/            ← 整体框架：Topbar + Sidebar + Main + ContextPanel + AgentComposer
    Sidebar/                    ← 左侧：页面导航 + 知识库列表 + 用户信息
    Topbar/                     ← 顶部栏
    ContextPanel/               ← 右侧：Sources + Search + Steps + Memory
    AgentComposer/              ← 底部全局 Agent 输入栏

  pages/
    Login/                      ← 新增：登录页 + 注册页
    DashboardPage/              ← 总览/仪表盘
    ChatPage/                   ← Agent 对话
    DocumentsPage/              ← 文档管理
    DocumentDetailPage/         ← 文档详情（含 PDF 预览）
    NotesPage/                  ← 笔记
    Knowledge/                  ← 新增：知识图谱（RAG 可视化）
    TasksPage/                  ← 新增：任务列表
    TaskDetailPage/             ← 任务详情/进度
    EvaluationPage/             ← 新增：评测管理
    SettingsPage/               ← 设置（模型配置、MCP 等）
    NotFoundPage/               ← 新增：404
    RouteErrorPage/             ← 新增：路由错误

  features/                     ← 按业务模块拆分（当前无 components/ 子目录，业务组件放在 pages/ 内）
    auth/                       ← 新增：登录/注册
    knowledge-bases/
    documents/
    chat/
    notes/
    tasks/
    mcp/
    evaluation/                 ← 新增：评测
    overview/                   ← 新增：总览/仪表盘数据
    settings/                   ← 新增：设置页数据

  lib/                          ← 工具函数
    apiClient.ts                ← REST API 客户端
    dateTime.ts                 ← 日期格式化
    fileUpload.ts               ← 文件上传
    sourceColor.ts              ← 来源颜色映射

  styles/                       ← 全局样式
    globals.css
    tokens.css                  ← 设计 Token（颜色、间距等）
    ui.module.css               ← 通用 UI 样式

  assets/                       ← 静态资源
    hero.png
    brain.png
    delete.svg
    toast/                      ← Toast 图标
```

原则：

- `pages/` 负责页面组合
- `features/` 负责业务模块
- `components/ui/` 放无业务含义的通用组件
- `layouts/` 放整体工作台结构
- `lib/` 放 API 客户端、SSE、格式化等工具

## 5. 状态管理设计

> 当前实现：localStorage 持久化 + React Context 全局状态 + useReducer/useState 局部状态。

### 5.1 持久化状态

由 localStorage 管理（`features/*/store.ts`）：

```text
认证 token & 用户信息     (features/auth/store.ts)
```

各业务模块通过 `api.ts` 中的 fetch 函数直接请求后端，组件内用 useState/useEffect 管理数据加载状态：

```text
知识库列表
文档列表
文档详情
笔记列表
对话历史
消息列表
任务状态
```

### 5.2 Client UI State

由 React Context 管理：

```text
主题切换（暗色/亮色）      (context/ThemeContext.tsx)
Ant Design 主题配置        (context/AntdConfig.tsx)
```

由页面局部 state 管理：

```text
当前知识库选择
当前会话
Composer 输入内容
右侧面板当前 tab
```

### 5.3 Streaming State

Chat 流式回答单独处理，由 `features/chat/stream.ts` 封装 SSE 连接和事件解析：

```text
流式回答文本
Agent 步骤
引用来源
工具调用状态
```

## 6. API 通信

> 当前实现：`lib/apiClient.ts` 统一封装 fetch，自动处理 token 注入和 401 跳转登录；各 `features/*/api.ts` 基于 apiClient 提供业务 API 函数。

普通数据请求使用 REST：

```text
GET  /api/v1/knowledge-bases
GET  /api/v1/knowledge-bases/:id/documents
GET  /api/v1/documents/:id
GET  /api/v1/conversations/:id
GET  /api/v1/knowledge-bases/:id/notes
```

上传使用 multipart：

```text
POST /api/v1/documents/upload
```

Chat 流式回答使用 SSE：

```text
POST /api/v1/chat/stream
```

前端统一处理 SSE 事件类型：

```text
message_delta
source_added
tool_started
tool_finished
step_updated
error
done
```

## 7. Agent Composer 设计

底部输入栏是全局能力，但要根据页面动态设置上下文。

Composer 状态：

```text
value
currentKbId
conversationId
contextType
contextIds
mode
attachments
```

`contextType` 示例：

```text
knowledge_base
conversation
document
documents
note
global
```

不同页面的 placeholder：

```text
总览：向当前知识库提问
对话：继续当前会话
文档：围绕选中文档提问
文档详情：围绕当前文档提问，或输入 /summarize
笔记：整理、改写或扩展当前笔记
设置：询问参数含义或生成推荐配置
```

## 8. 右侧 Context Panel

右侧面板建议做成可复用组件。

Tabs：

```text
Sources
Search
Steps
Memory
```

数据来源：

- `Sources`：当前回答引用来源
- `Search`：检索到的 chunks
- `Steps`：Agent 执行步骤
- `Memory`：用户偏好和当前上下文摘要

第一版可以只做：

```text
Sources + Steps
```

## 9. 模型配置页面

考虑到个人知识库通常涉及隐私资料，前端设置页需要提供用户自行配置模型的能力。

模型配置应支持三类模式：

```text
云模型 API
本地模型
私有部署模型
```

### 9.1 云模型 API

适合用户愿意调用托管模型，但不希望知识库原文被平台存储的场景。

配置项：

```text
Provider
Base URL
API Key
Chat Model
Embedding Model
数据发送策略
```

### 9.2 本地模型

适合完全本地运行。

可支持：

```text
Ollama
LM Studio
LocalAI
vLLM OpenAI Compatible Server
```

配置项：

```text
本地服务地址
聊天模型名
Embedding 模型名
连接测试
```

### 9.3 私有部署模型

适合公司内网、NAS、私有云部署。

建议兼容：

```text
OpenAI Compatible API
Azure OpenAI
自定义网关
```

### 9.4 数据策略

页面上需要明确告诉用户模型调用会发送什么数据。

建议提供：

```text
仅发送检索片段到模型
允许发送完整文档摘要
完全本地，不调用云模型
```

前端保存配置时不应在浏览器长期明文保存 API Key。推荐：

```text
API Key 提交给后端加密保存
前端只显示 masked key
支持测试连接
支持清除 key
```

模型配置相关组件：

```text
ModelProviderSelector
ModelConnectionForm
ApiKeyField
ModelNameSelect
EmbeddingModelSelect
ModelConnectionTest
DataPolicySelect
```

## 10. MCP 能力页面

MCP 用于让 Agent 连接外部工具、数据源和本地能力。前端需要提供 MCP Server 的配置、授权、调试和调用可视化。

建议第一版放在设置页里，后续再拆成独立页面：

```text
/kb/:kbId/settings
/mcp
```

### 10.1 页面能力

```text
查看已连接 MCP Server
新增 MCP Server
编辑启动方式和环境变量
启用 / 禁用 MCP Server
查看 Server 暴露的 tools / resources / prompts
测试连接
为知识库选择可用 MCP Server
配置 Agent 是否允许调用 MCP 工具
展示 MCP 工具调用记录
```

### 10.2 MCP Server 配置项

```text
名称
类型
传输方式
命令 / URL
环境变量
启用状态
作用范围
权限策略
```

传输方式：

```text
stdio
http
sse
```

作用范围：

```text
全局可用
仅当前知识库可用
仅当前会话可用
```

权限策略：

```text
只读工具自动允许
写入工具需要确认
高风险工具禁用
每次调用都确认
```

### 10.3 前端状态

MCP Server 属于 Server State，由 TanStack Query 管理：

```text
mcp server list
mcp server detail
mcp tools
mcp resources
mcp prompts
mcp connection status
```

临时 UI 状态由 Zustand / Context 管理：

```text
当前选中的 MCP Server
当前展开的 tool
新增 Server 表单
工具权限编辑状态
```

### 10.4 MCP 相关组件

```text
McpServerList
McpServerCard
McpConnectionForm
McpToolList
McpResourceList
McpPermissionMatrix
McpConnectionTest
McpCallHistory
McpApprovalDialog
```

### 10.5 Agent 调用 MCP 的前端表现

右侧 Context Panel 的 `Steps` 里需要展示：

```text
MCP 工具名称
调用参数摘要
调用状态
返回结果摘要
是否需要用户确认
```

如果工具有副作用，例如写文件、发请求、修改外部系统，需要弹出确认：

```text
Agent 想调用 notion.create_page
作用：在 Notion 中创建一条页面
参数摘要：标题、目标数据库
允许 / 拒绝
```

## 11. 关键组件

> 以下标注 ✅ 的已实现，其余为规划中的组件。

### WorkspaceLayout ✅

负责整体框架：

```text
Topbar ✅
Sidebar ✅
Main Outlet ✅
ContextPanel ✅
AgentComposer ✅
```

### Sidebar ✅

包含：

- 页面导航 ✅
- 知识库列表
- 左下角用户信息
- 设置入口 ✅

### AgentComposer ✅

底部全局输入栏，支持按页面动态设置上下文。

### ChatMessageList ✅

位于 `pages/ChatPage/`：

- 用户消息 ✅
- Agent 消息 ✅
- Markdown 渲染（react-markdown）✅
- 代码高亮（highlight.js）✅
- 流式输出 ✅
- 来源引用 chips ✅

### DocumentList ✅

位于 `pages/DocumentsPage/`：

- 文档状态
- 解析进度
- 上传入口
- 删除确认

### TaskDetail ✅

位于 `pages/TaskDetailPage/`，用于文档处理、批量导入等长任务进度展示。

### TaskProgress

用于文档处理、批量导入、摘要生成等长任务。

## 12. 错误与空状态

前端需要明确设计这些状态：

```text
空知识库
无文档
文档解析失败
无检索结果
回答无来源
模型调用失败
SSE 连接中断
上传超限
文件类型不支持
MCP Server 连接失败
MCP 工具调用失败
MCP 工具需要授权
```

尤其是 Agent 问答场景：

- 没有来源时不要假装知道
- 显示“未找到可靠来源”
- 提供“扩大检索范围”或“上传更多资料”的操作

## 13. 权限与确认

前端应对高风险操作加确认：

```text
删除文档
删除知识库
批量重解析
覆盖已有笔记
清空对话
```

Agent 可直接执行的低风险操作：

```text
创建新笔记
生成摘要草稿
生成问题建议
生成标签建议
```

MCP 工具权限建议：

```text
只读 MCP 工具：可自动执行
写入 MCP 工具：执行前确认
外部系统修改：执行前确认
批量操作：执行前确认
危险工具：默认禁用
```

## 14. UI 风格原则

建议保持简洁工作台风格：

- 避免营销式大 hero
- 避免过多卡片嵌套
- 中间主区域保持单层结构
- 右侧只展示当前任务相关信息
- 常用操作靠近当前上下文
- 底部 Composer 全局可用，但上下文要明确

## 15. 前端开发阶段

### 阶段 1：静态工作台 ✅

```text
布局 ✅
页面切换 ✅
文档列表 ✅
笔记列表 ✅
设置表单 ✅
```

### 阶段 2：接入 API ✅

```text
知识库 CRUD ✅
文档上传 ✅
文档状态 ✅
笔记列表 ✅
对话历史 ✅
登录/注册 ✅
```

### 阶段 3：流式 Agent ✅

```text
SSE Chat ✅
流式回答 ✅
Sources ✅
Steps ✅
任务进度 ✅
```

### 阶段 4：体验完善（进行中）

```text
错误状态 ✅
空状态 ✅
快捷命令
文档选择上下文
保存为笔记 ✅
响应式适配
MCP 工具调用步骤展示 ✅
MCP 权限确认
MCP 连接测试
评测中心 ✅
暗色/亮色主题切换 ✅
```

## 16. 审核重点

建议重点审核：

```text
1. 是否采用全局底部 Agent 输入栏
2. 右侧 Context Panel 是否第一版就保留
3. 前端是 Vite 单页应用，还是 Next.js
4. 是否需要复杂 Markdown 编辑器
5. 文档详情页是否需要 PDF 原文预览
6. Chat、文档、笔记之间的上下文联动是否清晰
7. MCP 配置放在设置页，还是做独立页面
8. MCP 工具调用是否需要默认人工确认
9. 第一版是否只支持 stdio MCP，还是同时支持 HTTP/SSE
```
