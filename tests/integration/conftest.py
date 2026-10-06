import pytest
from fastapi.testclient import TestClient

from app.core.composition import get_validation_service
from app.main import app
from app.services.validation_service import ValidationService

MAX_SIZE_BYTES = 5 * 1024 * 1024


class ServicioQueFalla:
    """Doble de test: simula un error no previsto dentro del servicio."""

    def validate(self, archivo_base64: str, nombre: str):
        raise RuntimeError("falla inesperada")


@pytest.fixture
def client():
    """Cliente HTTP con el servicio armado por el test: el límite no depende del
    .env local."""
    app.dependency_overrides[get_validation_service] = lambda: ValidationService(
        max_size_bytes=MAX_SIZE_BYTES
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def failing_client():
    """Cliente HTTP cuyo servicio lanza una excepción no controlada."""
    app.dependency_overrides[get_validation_service] = ServicioQueFalla
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()
