

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.log_instance import app_logger


engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_engine() -> tuple[async_sessionmaker[AsyncSession], AsyncEngine] | None:
    global engine, AsyncSessionLocal

    if engine is not None and AsyncSessionLocal is not None:
        return

    settings = get_settings()
    try:
        engine = create_async_engine(
            settings.database_url, 
            **settings.database_options.model_dump(),
        )
        
        AsyncSessionLocal = async_sessionmaker(
            engine, 
            expire_on_commit=False,     
            autocommit=False,               # 禁用自动提交    
            autoflush=False,                # 禁用自动flush        
        )
        app_logger.info("数据库连接成功")
        return AsyncSessionLocal, engine
    
    except Exception as e:
        app_logger.error(f"数据库连接失败, error: {e}")
        raise Exception(f"数据库连接失败, error: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        await init_engine()

    assert AsyncSessionLocal is not None

    async with AsyncSessionLocal() as db:
        yield db


async def get_session_local() -> async_sessionmaker:
    if AsyncSessionLocal is None:
        await init_engine()

    assert AsyncSessionLocal is not None

    return AsyncSessionLocal


async def close_db_engine() -> None:
    global engine, AsyncSessionLocal
    if engine is None:
        return
        
    await engine.dispose()
    engine = None
    AsyncSessionLocal = None
    app_logger.info("数据库连接关闭")

