import time
import uuid
from contextvars import ContextVar
from collections.abc import Callable

from fastapi import FastAPI, Request
from starlette.responses import Response


request_id_ctx: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


def generate_request_id() -> str:
    """
    生成请求ID
    """
    return uuid.uuid4().hex


def get_request_id() -> str:
    """
    当前协程获取 request_id
    """
    return request_id_ctx.get()


def install_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:

        # 支持 nginx / gateway 透传
        request_id = request.headers.get("x-request-id")

        # 防御超长 Header
        if not request_id:
            request_id = generate_request_id()

        request.state.request_id = request_id

        # 写入 ContextVar
        token = request_id_ctx.set(request_id)

        try:
            response = await call_next(request)

        except Exception:
            # 即使异常也带回 request_id
            response = Response(
                content="Internal Server Error",
                status_code=500,
            )

        finally:
            request_id_ctx.reset(token)

        response.headers["X-Request-Id"] = request_id

        return response


