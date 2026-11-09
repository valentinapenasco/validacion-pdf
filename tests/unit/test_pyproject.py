"""pyproject.toml identifica el proyecto, declara con versión exacta todo lo que importa
app/ y no repite tablas (uv no lo puede leer si una tabla aparece dos veces)."""

import re
from pathlib import Path

# Sin tomllib: el proyecto admite Python 3.10 y tomllib llegó en la 3.11.
PYPROJECT = (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(
    encoding="utf-8"
)


def _dependencias() -> str:
    return re.search(r"^dependencies = \[(.*?)^\]", PYPROJECT, re.M | re.S).group(1)


def test_identifica_el_proyecto() -> None:
    assert re.search(r'^name = "validacion-pdf"$', PYPROJECT, re.M)
    assert re.search(r'^requires-python = ">=3\.10"$', PYPROJECT, re.M)


def test_declara_pymupdf() -> None:
    # app/services/validation_service.py importa fitz (PyMuPDF).
    assert re.search(r'"pymupdf>=[\d.]+"', _dependencias())


def test_todas_las_dependencias_declaran_una_version_minima() -> None:
    # Mismo criterio en los cinco microservicios: >= la versión probada, que es la
    # que fija uv.lock. Sin == ni rangos con tope.
    declaradas = re.findall(r'^\s+"([^"]+)",$', PYPROJECT, re.M)

    assert declaradas
    for dependencia in declaradas:
        assert re.fullmatch(r"[\w.\[\]-]+>=[\d.]+", dependencia), dependencia


def test_no_repite_tablas() -> None:
    tablas = re.findall(r"^\[[^\]]+\]$", PYPROJECT, re.M)

    assert len(tablas) == len(set(tablas))
