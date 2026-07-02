from app.core.log_instance import app_logger

from app.core.config import get_settings
settings = get_settings()

async def install_events() -> None:
    try:
        from app.db.base import Base
        from app.db.session import engine
        from app.models import init_model
        init_model()

        assert engine is not None
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        app_logger.info("database tables created successfully")
        
    except Exception as e:
        app_logger.error(f"failed to create database tables, error: {e}")

