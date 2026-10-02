from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import PdfValidationError
from app.schemas.validation_request import ValidationRequest
from app.services.validation_service import ValidationService

router = APIRouter(tags=["Validación PDF"])


@router.get("/health")
@router.get("/api/v1/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/validar")
@router.post("/api/v1/validar")
async def validar_pdf(payload: ValidationRequest, request: Request) -> dict:
    try:
        resultado = ValidationService().validate(payload.archivo_base64, payload.nombre)
        return {
            "valido": resultado.valido,
            "nombre": resultado.nombre,
            "tamano_bytes": resultado.tamano_bytes,
        }
    except PdfValidationError as exc:
        error = {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": request.state.correlation_id,
        }
        return JSONResponse(
            status_code=exc.status_code,
            content={"valido": False, "error": error},
        )
