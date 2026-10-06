from functools import lru_cache

from app.core.config import settings
from app.services.validation_service import ValidationService


@lru_cache
def get_validation_service() -> ValidationService:
    """Único lugar donde se arma el servicio con su configuración. Los tests lo
    sustituyen con app.dependency_overrides."""
    return ValidationService(max_size_bytes=settings.pdf_max_size_mb * 1024 * 1024)
