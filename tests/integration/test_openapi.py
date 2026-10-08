"""Swagger (/docs) publica la versión del proyecto: la de pyproject.toml, que es la
misma que el tag de la imagen."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_openapi_publica_la_version_del_proyecto() -> None:
    # Sin tomllib: el proyecto admite Python 3.10 y tomllib llegó en la 3.11.
    texto = PYPROJECT.read_text(encoding="utf-8")
    version = re.search(r'^version = "(.+)"$', texto, re.MULTILINE).group(1)

    respuesta = TestClient(app).get("/openapi.json")

    assert respuesta.json()["info"]["version"] == version
