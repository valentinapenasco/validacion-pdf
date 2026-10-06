from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.controllers.validation_controller import router as validation_router
from app.core.config import settings
from app.core.exceptions import PdfValidationError

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservicio para validar archivos PDF en Base64",
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("x-correlation-id") or str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


def error_response(
    request: Request, status_code: int, code: str, message: str, details: dict
) -> JSONResponse:
    """Formato común de errores del contrato microservicios-pdf. El header se
    agrega acá porque el handler de Exception corre fuera del middleware."""
    correlation_id = request.state.correlation_id
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
        {"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    return error_response(
        request, 500, "INTERNAL_ERROR", "Error interno del servidor", {}
    )


app.include_router(validation_router)
