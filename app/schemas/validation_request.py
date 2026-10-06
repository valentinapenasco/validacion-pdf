from pydantic import BaseModel, Field, field_validator


class ValidationRequest(BaseModel):
    archivo_base64: str = Field(..., min_length=1)
    nombre: str = Field(..., min_length=1, max_length=255)

    @field_validator("archivo_base64")
    @classmethod
    def validar_archivo_base64(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("archivo_base64 no puede estar vacío")
        return value.strip()


class ValidationResponse(BaseModel):
    valido: bool
    nombre: str | None = None
    tamano_bytes: int | None = None
    error: dict | None = None
