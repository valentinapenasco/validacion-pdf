import base64
import binascii
import logging

from app.core.exceptions import PdfValidationError
from app.models.pdf_validation_result import PdfValidationResult

logger = logging.getLogger(__name__)


def _pdf_invalido() -> PdfValidationError:
    return PdfValidationError(
        code="PDF_INVALID",
        message="El archivo no es un PDF válido",
        status_code=422,
    )


class ValidationService:
    def __init__(self, max_size_bytes: int) -> None:
        self._max_size_bytes = max_size_bytes

    def validate(self, archivo_base64: str, nombre: str) -> PdfValidationResult:
        sin_espacios = "".join(archivo_base64.split())
        try:
            decoded = base64.b64decode(sin_espacios, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise _pdf_invalido() from exc

        if not decoded:
            raise _pdf_invalido()

        if len(decoded) > self._max_size_bytes:
            raise PdfValidationError(
                code="PDF_TOO_LARGE",
                message="El archivo supera el tamaño máximo permitido",
                status_code=413,
                details={
                    "max_size_bytes": self._max_size_bytes,
                    "received_size_bytes": len(decoded),
                },
            )

        if not decoded.startswith(b"%PDF"):
            raise _pdf_invalido()

        if b"%%EOF" not in decoded:
            raise PdfValidationError(
                code="PDF_CORRUPTED",
                message="El archivo PDF está corrupto",
                status_code=422,
            )

        # Sin el nombre ni el contenido (contrato 1.2.0): pueden tener datos personales.
        logger.info("pdf valido tamano_bytes=%d", len(decoded))
        return PdfValidationResult(
            valido=True,
            nombre=nombre,
            tamano_bytes=len(decoded),
        )
