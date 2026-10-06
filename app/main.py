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


@app.exception_handler(PdfValidationError)
async def validation_exception_handler(request: Request, exc: PdfValidationError):
    correlation_id = request.state.correlation_id
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "valido": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": correlation_id,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={
            "valido": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "El request no cumple el contrato esperado",
                "details": {"errors": exc.errors()},
                "correlation_id": request.state.correlation_id,
            },
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    # Corre fuera del middleware de correlation ID: el header se agrega acá.
    correlation_id = request.state.correlation_id
    return JSONResponse(
        status_code=500,
        content={
            "valido": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor",
                "details": {},
                "correlation_id": correlation_id,
            },
        },
        headers={"X-Correlation-ID": correlation_id},
    )


app.include_router(validation_router)
