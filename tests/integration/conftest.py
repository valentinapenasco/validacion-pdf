import pytest
from fastapi.testclient import TestClient

from app.core.composition import get_validation_service
from app.main import app
from app.services.validation_service import ValidationService

MAX_SIZE_BYTES = 5 * 1024 * 1024


@pytest.fixture
def client():
    """Cliente HTTP con el servicio armado por el test: el límite no depende del
    .env local."""
    app.dependency_overrides[get_validation_service] = lambda: ValidationService(
        max_size_bytes=MAX_SIZE_BYTES
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
