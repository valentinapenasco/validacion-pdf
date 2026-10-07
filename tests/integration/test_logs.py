import base64
import logging

from fastapi.testclient import TestClient

from app.main import app

PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nContenido privado\n%%EOF"
PDF_REQUEST = {
    "archivo_base64": base64.b64encode(PDF).decode("ascii"),
    "nombre": "contrato-de-juan-perez.pdf",
}


def _mensajes(caplog) -> list[str]:
    return [record.getMessage() for record in caplog.records]


def test_validacion_aceptada_registra_el_tamano(client, caplog):
    caplog.set_level(logging.INFO)

    client.post("/validar", json=PDF_REQUEST, headers={"X-Correlation-ID": "cid-1"})

    eventos = [r for r in caplog.records if "pdf valido" in r.getMessage()]
    assert len(eventos) == 1
    assert eventos[0].levelno == logging.INFO
    assert f"tamano_bytes={len(PDF)}" in eventos[0].getMessage()
    assert eventos[0].correlation_id == "cid-1"


def test_los_logs_no_incluyen_datos_sensibles(client, caplog):
    caplog.set_level(logging.DEBUG)

    client.post("/validar", json=PDF_REQUEST)

    todo = "\n".join(_mensajes(caplog))
    assert "juan-perez" not in todo
    assert "Contenido privado" not in todo
    assert PDF_REQUEST["archivo_base64"] not in todo


def test_el_acceso_se_registra_con_el_correlation_id_del_request(client, caplog):
    caplog.set_level(logging.INFO)

    client.get("/health", headers={"X-Correlation-ID": "cid-2"})

    accesos = [r for r in caplog.records if "path=/health" in r.getMessage()]
    assert len(accesos) == 1
    assert accesos[0].correlation_id == "cid-2"
    assert "correlation_id=" not in accesos[0].getMessage()


def test_registra_inicio_y_apagado_ordenados(caplog):
    caplog.set_level(logging.INFO)

    with TestClient(app):
        pass

    mensajes = _mensajes(caplog)
    assert "servicio iniciado" in mensajes
    assert mensajes.index("apagado iniciado") < mensajes.index("apagado completo")
