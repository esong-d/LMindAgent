from functools import wraps
import time

from loguru import logger


def time_cost(name: str = "", _logger: logger = logger):  # type: ignore
    """异步函数耗时装饰器

    Args:
        name: 自定义名称，用于日志输出；为空则使用函数名
        _logger: loguru logger 实例
    """
    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            label = name or func.__name__
            _logger.info(f"{label} cost time: {elapsed:.3f}s")

            return result

        return wrapper

    return decorator
