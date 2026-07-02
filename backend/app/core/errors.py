

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status


class AppError(Exception):

    def __init__(
        self, 
        message: str = "Bad request", *, 
        code: int = 400, 
        status_code: int = status.HTTP_400_BAD_REQUEST, 
        detail: Any | None = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found", *, code: int = 404, detail: Any | None = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", *, code: int = 403, detail: Any | None = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", *, code: int = 401, detail: Any | None = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", *, code: int = 400, detail: Any | None = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class PreconditionFailedError(AppError):
    def __init__(
        self, message: str = "Precondition failed", *, code: int = 412, detail: Any | None = None
    ):
        super().__init__(code=code, message=message, status_code=status.HTTP_412_PRECONDITION_FAILED, detail=detail)


def ok(data: Any = None) -> dict[str, Any]:
    return {"success": True, "data": data}


def fail(code: int, message: str, *, detail: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"success": False, "error": {"code": code, "message": message}}
    if detail is not None:
        payload["error"]["detail"] = detail
    return payload


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=fail(exc.code, exc.message, detail=exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=fail(422, "Request validation error", detail=exc.errors()),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=fail(500, "Internal server error"),
        )
