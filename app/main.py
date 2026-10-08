import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.controllers.validation_controller import router as validation_router
from app.core.config import settings
from app.core.exceptions import PdfValidationError
from app.core.logs import configurar_logs, correlation_id_actual

configurar_logs(settings.log_level)
logger = logging.getLogger("validacion_pdf")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("servicio iniciado")
    yield
    # uvicorn llega acá ante SIGTERM, después de cerrar el puerto y terminar las
    # requests en curso (12-Factor IX). Validación no tiene conexiones que cerrar.
    logger.info("apagado iniciado")
    logger.info("apagado completo")


app = FastAPI(
    title=settings.app_name,
    version="1.0.3",
    description="Microservicio para validar archivos PDF en Base64",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("x-correlation-id") or str(uuid4())
    request.state.correlation_id = correlation_id
    token = correlation_id_actual.set(correlation_id)
    inicio = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        logger.info(
            "method=%s path=%s status=%s duracion_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - inicio) * 1000,
        )
        return response
    finally:
        correlation_id_actual.reset(token)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict,
    exc_info: BaseException | None = None,
) -> JSONResponse:
    """Formato común de errores del contrato microservicios-pdf. El header se
    agrega acá porque el handler de Exception corre fuera del middleware."""
    correlation_id = request.state.correlation_id
    logger.log(
        logging.ERROR if status_code >= 500 else logging.WARNING,
        "code=%s status=%s message=%s",
        code,
        status_code,
        message,
        exc_info=exc_info,
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "valido": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "correlation_id": correlation_id,
            },
        },
        headers={"X-Correlation-ID": correlation_id},
    )


@app.exception_handler(PdfValidationError)
async def validation_exception_handler(request: Request, exc: PdfValidationError):
    return error_response(request, exc.status_code, exc.code, exc.message, exc.details)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return error_response(
        request,
        400,
        "VALIDATION_ERROR",
        "El request no cumple el contrato esperado",
        {"errors": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    return error_response(
        request, 500, "INTERNAL_ERROR", "Error interno del servidor", {}, exc
    )


app.include_router(validation_router)
