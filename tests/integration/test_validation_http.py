import base64
import logging

VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] >>\n"
    b"endobj\n%%EOF"
)


def encoded_pdf(content: bytes = VALID_PDF) -> str:
    return base64.b64encode(content).decode("ascii")


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"]


def test_validation_endpoint_returns_success_contract(client):
    response = client.post(
        "/validar",
        json={
            "archivo_base64": encoded_pdf(),
            "nombre": "contrato.pdf",
        },
        headers={"X-Correlation-ID": "abc-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "abc-123"
    assert response.json() == {
        "valido": True,
        "nombre": "contrato.pdf",
        "tamano_bytes": len(VALID_PDF),
    }


def test_validation_endpoint_returns_standard_error_contract(client):
    response = client.post(
        "/validar",
        json={"archivo_base64": "no-es-base64", "nombre": "archivo.pdf"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["valido"] is False
    assert body["error"]["code"] == "PDF_INVALID"
    assert body["error"]["message"]
    assert body["error"]["details"] == {}
    assert body["error"]["correlation_id"]
    assert response.headers["X-Correlation-ID"]


def test_validation_endpoint_rejects_corrupted_pdf(client):
    corrupted_pdf = b"%PDF-1.4\ncontenido incompleto"

    response = client.post(
        "/validar",
        json={"archivo_base64": encoded_pdf(corrupted_pdf), "nombre": "archivo.pdf"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PDF_CORRUPTED"


def test_validation_endpoint_rejects_pdf_that_is_too_large(client):
    oversized_pdf = b"%PDF-1.4\n" + (b"x" * (6 * 1024 * 1024))

    response = client.post(
        "/validar",
        json={"archivo_base64": encoded_pdf(oversized_pdf), "nombre": "archivo.pdf"},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PDF_TOO_LARGE"


def test_error_preserves_supplied_correlation_id(client):
    correlation_id = "error-123"

    response = client.post(
        "/validar",
        json={"archivo_base64": "no-es-base64", "nombre": "archivo.pdf"},
        headers={"X-Correlation-ID": correlation_id},
    )

    assert response.status_code == 422
    assert response.headers["X-Correlation-ID"] == correlation_id
    assert response.json()["error"]["correlation_id"] == correlation_id


def test_error_uses_same_generated_correlation_id_in_header_and_body(client):
    response = client.post(
        "/validar",
        json={"archivo_base64": "no-es-base64", "nombre": "archivo.pdf"},
    )

    assert response.status_code == 422
    assert (
        response.headers["X-Correlation-ID"]
        == response.json()["error"]["correlation_id"]
    )


def test_validation_endpoint_rejects_missing_base64(client):
    response = client.post(
        "/validar",
        json={"nombre": "archivo.pdf"},
    )

    assert response.status_code == 400
    assert response.json()["valido"] is False
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.headers["X-Correlation-ID"]


def test_validation_endpoint_rejects_missing_nombre(client):
    response = client.post("/validar", json={"archivo_base64": encoded_pdf()})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unexpected_error_returns_internal_error_contract(failing_client):
    response = failing_client.post(
        "/validar",
        json={"archivo_base64": encoded_pdf(), "nombre": "contrato.pdf"},
        headers={"X-Correlation-ID": "falla-500"},
    )

    assert response.status_code == 500
    body = response.json()
    assert body["valido"] is False
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"]
    assert body["error"]["details"] == {}
    assert body["error"]["correlation_id"] == "falla-500"
    assert response.headers["X-Correlation-ID"] == "falla-500"


def test_validation_endpoint_rejects_blank_base64(client):
    response = client.post(
        "/validar", json={"archivo_base64": "   ", "nombre": "contrato.pdf"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_request_log_includes_correlation_id(client, caplog):
    caplog.set_level(logging.INFO, logger="validacion_pdf")

    client.get("/health", headers={"X-Correlation-ID": "log-123"})

    assert "correlation_id=log-123" in caplog.text
    assert "path=/health" in caplog.text


def test_error_log_includes_code_and_correlation_id(client, caplog):
    caplog.set_level(logging.INFO, logger="validacion_pdf")

    client.post(
        "/validar",
        json={"archivo_base64": "no-es-base64", "nombre": "contrato.pdf"},
        headers={"X-Correlation-ID": "log-error"},
    )

    assert "correlation_id=log-error code=PDF_INVALID" in caplog.text
