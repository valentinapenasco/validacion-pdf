"""Swagger (/docs) publica la versión del proyecto: la de pyproject.toml, que es la
misma que el tag de la imagen."""

from pathlib import Path

import tomllib
from fastapi.testclient import TestClient

from app.main import app

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_openapi_publica_la_version_del_proyecto() -> None:
    proyecto = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]

    respuesta = TestClient(app).get("/openapi.json")

    assert respuesta.json()["info"]["version"] == proyecto["version"]
