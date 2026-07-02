import sys
from pathlib import Path

from loguru import logger

from app.core.config import get_settings
from app.middleware.request_id import get_request_id
from app.core.log_instance import app_logger

settings = get_settings()

LOG_DIR = Path(settings.logger_file_path)
LOG_DIR.mkdir(parents=True, exist_ok=True)


LOG_FORMAT = (
    "[{time:YYYY-MM-DD HH:mm:ss}] | "
    "{level:<8} | "
    "{extra[request_id]} | "
    "{extra[module]} | "
    "{file}:{line} | "
    "{extra[client_ip]} | "
    "{message}"
)


def _patch_record(record: dict) -> None:
    """
    自动补充日志上下文
    """

    record["extra"].setdefault(
        "request_id",
        get_request_id(),
    )

    record["extra"].setdefault(
        "module",
        "app",
    )

    record["extra"].setdefault(
        "client_ip",
        "-",
    )


def setup_logger() -> None:
    """
    初始化日志
    """

    logger.remove()

    logger.configure(
        patcher=_patch_record
    )

    #
    # 控制台
    #
    logger.add(
        sys.stdout,
        level="INFO",
        colorize=True,
        format=LOG_FORMAT,
    )

    #
    # 全局日志
    #
    logger.add(
        LOG_DIR / "app_{time:YYYY-MM}.log",
        level="INFO",
        encoding="utf-8",
        enqueue=True,
        retention="1 month",
        format=LOG_FORMAT,
    )

    #
    # HTTP访问日志
    #
    logger.add(
        LOG_DIR / "access_{time:YYYY-MM}.log",
        level="INFO",
        encoding="utf-8",
        enqueue=True,
        retention="1 month",
        filter=lambda r: r["extra"].get("module") == "http",
        format=LOG_FORMAT,
    )

    #
    # DB
    #
    logger.add(
        LOG_DIR / "db_{time:YYYY-MM}.log",
        level="DEBUG",
        encoding="utf-8",
        enqueue=True,
        retention="1 month",
        filter=lambda r: r["extra"].get("module") == "db",
        format=LOG_FORMAT,
    )

    #
    # RAG
    #
    logger.add(
        LOG_DIR / "rag_{time:YYYY-MM}.log",
        level="DEBUG",
        encoding="utf-8",
        enqueue=True,
        retention="1 month",
        filter=lambda r: r["extra"].get("module") == "rag",
        format=LOG_FORMAT,
    )

    #
    # LLM
    #
    logger.add(
        LOG_DIR / "llm_{time:YYYY-MM}.log",
        level="DEBUG",
        encoding="utf-8",
        enqueue=True,
        retention="1 month",
        filter=lambda r: r["extra"].get("module") == "llm",
        format=LOG_FORMAT,
    )

    #
    # Redis
    #
    logger.add(
        LOG_DIR / "redis_{time:YYYY-MM}.log",
        level="DEBUG",
        encoding="utf-8",
        enqueue=True,
        retention="1 month",
        filter=lambda r: r["extra"].get("module") == "redis",
        format=LOG_FORMAT,
    )

    #
    # Worker
    #
    logger.add(
        LOG_DIR / "worker_{time:YYYY-MM}.log",
        level="DEBUG",
        encoding="utf-8",
        enqueue=True,
        retention="1 month",
        filter=lambda r: r["extra"].get("module") == "worker",
        format=LOG_FORMAT,
    )

    app_logger.info("日志初始化完成")


