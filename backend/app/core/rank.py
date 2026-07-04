
import threading

from app.rag.re_ranker import BGEReranker, RerankerManager
from app.core.log_instance import app_logger


rank_manager: RerankerManager | None = None
_rank_lock = threading.Lock()


def init_rank_manager():
    global rank_manager

    if rank_manager is not None:
        return rank_manager

    with _rank_lock:
        if rank_manager is not None:
            return rank_manager

        rank_manager = RerankerManager()
        app_logger.info("Rank model manager initialized")

    return rank_manager


def get_rank_manager() -> RerankerManager:
    if rank_manager is None:
        return init_rank_manager()
    
    return rank_manager


async def close_rank_manager():
    global rank_manager

    if rank_manager:
        await rank_manager.close()
        rank_manager = None