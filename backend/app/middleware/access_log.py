import time
from fastapi import FastAPI, Request

from app.core.log_instance import http_logger

def _get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        forwarded_ip = x_forwarded_for.split(",")[0].strip()
        if forwarded_ip:
            return forwarded_ip

    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()

    if request.client:
        return request.client.host

    return "-"


def _get_url(request: Request) -> str:
    """返回 path + query string, 不包含 scheme 和 host"""
    if request.url.query:
        return f"{request.url.path}?{request.url.query}"
    return request.url.path


def install_logging_middleware(app: FastAPI):
    @app.middleware("http")
    async def logging_middleware(
        request: Request,
        call_next,
    ):
        start = time.perf_counter()

        try:
            response = await call_next(request)

            cost = (time.perf_counter() - start)
            # 请求结束时记录日志
            request_id = getattr(request.state, "request_id", "-")

            client_ip = _get_client_ip(request)

            http_logger.bind(request_id=request_id, client_ip=client_ip).info(
                "{} {} {} {:.3f}s",
                request.method,
                _get_url(request),
                response.status_code,
                cost,
            )

            return response

        except Exception:
            cost = (
                time.perf_counter() - start
            )

            request_id = getattr(request.state, "request_id", "-")
            client_ip = _get_client_ip(request)

            http_logger.bind(request_id=request_id, client_ip=client_ip).exception(
                "{} {} 500 {:.3f}s",
                request.method,
                _get_url(request),
                cost,
            )

            raise
