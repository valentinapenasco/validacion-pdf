import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logs import configurar_logs, correlation_id_actual


@pytest.fixture
def logging_restaurado():
    """configurar_logs reemplaza los handlers del root: se restauran al terminar."""
    root = logging.getLogger()
    handlers, nivel = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(nivel)


def test_log_level_por_defecto_es_info(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    assert Settings(_env_file=None).log_level == "INFO"


def test_log_level_invalido_impide_arrancar(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_configurar_logs_aplica_el_nivel(logging_restaurado):
    configurar_logs("DEBUG")

    assert logging.getLogger().level == logging.DEBUG


def test_cada_linea_lleva_nivel_logger_y_correlation_id(logging_restaurado, capsys):
    configurar_logs("INFO")
    token = correlation_id_actual.set("cid-123")
    try:
        logging.getLogger("prueba").info("evento clave=valor")
    finally:
        correlation_id_actual.reset(token)

    assert "INFO prueba correlation_id=cid-123 evento clave=valor" in (
        capsys.readouterr().out
    )


def test_fuera_de_una_request_el_correlation_id_es_guion(logging_restaurado, capsys):
    configurar_logs("INFO")

    logging.getLogger("prueba").info("inicio")

    assert "correlation_id=- inicio" in capsys.readouterr().out
