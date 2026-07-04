

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings, init_langsmith
from app.core.errors import install_exception_handlers
from app.core.events import install_events
from app.core.rank import close_rank_manager, init_rank_manager
from app.db.session import init_engine, close_db_engine
from app.db.redis_db.client import get_redis_client, close_redis_client
from app.middleware.request_id import install_request_id_middleware
from app.middleware.access_log import install_logging_middleware
from app.api.routes import init_routers_v1
from app.core.log import setup_logger



@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在这里可以添加应用启动时需要执行的代码，例如连接数据库、加载模型等
    setup_logger()
    # 配置langsmith
    init_langsmith()

    # 数据库
    await init_engine()

    # 缓存
    await get_redis_client()

    await install_events() 

    # 初始化rank模型管理器
    init_rank_manager()
    
    yield
    
    # 在这里可以添加应用关闭时需要执行的代码，例如关闭数据库连接、清理资源等
    await close_redis_client()
    await close_db_engine()

    await close_rank_manager()



def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.project_name,
        description=settings.project_description,
        version=settings.project_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    install_request_id_middleware(app)
    install_logging_middleware(app)
    install_exception_handlers(app)

    # 注册路由
    init_routers_v1(app)

    return app


__all__ = [
    "create_app"
]
