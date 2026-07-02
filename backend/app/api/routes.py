
from fastapi import FastAPI

from app.core.config import get_settings

from app.api.v1 import home as home_router
from app.api.v1 import auth as auth_router
from app.api.v1 import chat as chat_router
from app.api.v1 import documents as documents_router
from app.api.v1 import files as files_router
from app.api.v1 import knowledge_bases as knowledge_bases_router
from app.api.v1 import mcp as mcp_router
from app.api.v1 import model_configs as model_configs_router
from app.api.v1 import notes as notes_router
from app.api.v1 import tasks as tasks_router
from app.api.v1 import evaluation as evaluation_router
from app.api.v1 import users as users_router

settings = get_settings()

def init_routers_v1(app: FastAPI):
    _prefix = f"{settings.api_prefix}/v1"

    app.include_router(home_router.router, prefix=_prefix, tags=["首页模块"])
    app.include_router(auth_router.router, prefix=_prefix, tags=["认证模块"])
    app.include_router(users_router.router, prefix=_prefix, tags=["用户模块"])
    app.include_router(knowledge_bases_router.router, prefix=_prefix, tags=["知识库模块"])
    app.include_router(documents_router.router, prefix=_prefix, tags=["文档模块"])
    app.include_router(chat_router.router, prefix=_prefix, tags=["聊天模块"])
    app.include_router(notes_router.router, prefix=_prefix, tags=["笔记模块"])
    app.include_router(tasks_router.router, prefix=_prefix, tags=["任务模块"])
    app.include_router(mcp_router.router, prefix=_prefix, tags=["MCP模块"])
    app.include_router(model_configs_router.router, prefix=_prefix, tags=["模型配置模块"])
    app.include_router(evaluation_router.router, prefix=_prefix, tags=["测评模块"])
    app.include_router(files_router.router, prefix=_prefix, tags=["文件模块"])

