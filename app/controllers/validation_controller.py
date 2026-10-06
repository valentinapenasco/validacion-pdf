from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.composition import get_validation_service
from app.schemas.validation_request import ValidationRequest, ValidationResponse
from app.services.validation_service import ValidationService

router = APIRouter(tags=["Validación PDF"])

ValidationServiceDep = Annotated[ValidationService, Depends(get_validation_service)]


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/validar")
async def validar_pdf(
    payload: ValidationRequest, service: ValidationServiceDep
) -> ValidationResponse:
    resultado = service.validate(payload.archivo_base64, payload.nombre)
    return ValidationResponse(
        valido=resultado.valido,
        nombre=resultado.nombre,
        tamano_bytes=resultado.tamano_bytes,
    )
