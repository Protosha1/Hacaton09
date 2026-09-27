# app/core/error_handlers.py
import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class UTF8JSONResponse(JSONResponse):
    """JSONResponse that declares its charset explicitly (see app/main.py).

    Starlette's default JSONResponse sends "Content-Type: application/json"
    without a charset. The body itself is correctly UTF-8 encoded, but some
    proxies / CDNs / older HTTP clients guess a different default encoding
    when no charset is declared — which is how Cyrillic text (e.g. the rank
    name "Ученик школы диалога") can turn into mojibake on the way to the
    browser. Declaring the charset removes that ambiguity.
    """
    media_type = "application/json; charset=utf-8"


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Return 422 with details.
    Uses jsonable_encoder because Pydantic custom validators may put
    non-serializable objects into exc.errors()['ctx'].
    """
    return UTF8JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "error": "Validation error",
            "details": exc.errors(),
            "path": str(request.url),
        }),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error on {request.url}: {exc}", exc_info=True)
    return UTF8JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        # Ключ должен быть "detail" — именно его читает фронтенд в unwrap()
        # (src/lib/api.js). С ключом "error" фронт не видел это сообщение
        # вообще и показывал общий текст "Что-то пошло не так", что и
        # маскировало реальные ошибки (например, сбой распознавания речи).
        content={"detail": "Ошибка базы данных. Попробуйте ещё раз."},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return UTF8JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера. Попробуйте ещё раз."},
    )