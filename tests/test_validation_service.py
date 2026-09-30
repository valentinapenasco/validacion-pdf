import base64

from fastapi.testclient import TestClient

from app.main import app


def test_health_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validar_pdf_valido():
    pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] >>\nendobj\n%%EOF"
    payload = {
        "archivo_base64": base64.b64encode(pdf).decode("ascii"),
        "nombre": "documento.pdf",
    }

    client = TestClient(app)
    response = client.post("/validar", json=payload, headers={"X-Correlation-ID": "abc-123"})

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "abc-123"
    assert response.json()["valido"] is True
    assert response.json()["nombre"] == "documento.pdf"
    assert response.json()["tamano_bytes"] == len(pdf)


def test_validar_pdf_base64_invalido():
    client = TestClient(app)
    response = client.post(
        "/validar",
        json={"archivo_base64": "no-es-base64", "nombre": "archivo.pdf"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["valido"] is False
    assert body["error"]["code"] == "PDF_INVALID"


def test_validar_pdf_demasiado_grande():
    pdf = b"%PDF-1.4" + (b"x" * (6 * 1024 * 1024))
    payload = {
        "archivo_base64": base64.b64encode(pdf).decode("ascii"),
        "nombre": "grande.pdf",
    }

    client = TestClient(app)
    response = client.post("/validar", json=payload)

    assert response.status_code == 413
    body = response.json()
    assert body["valido"] is False
    assert body["error"]["code"] == "PDF_TOO_LARGE"
    assert body["error"]["details"]["max_size_bytes"] == 5 * 1024 * 1024


def test_validar_pdf_con_nombre_omitido():
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] >>\nendobj\n"
        b"%%EOF"
    )
    payload = {"archivo_base64": base64.b64encode(pdf).decode("ascii")}

    client = TestClient(app)
    response = client.post("/validar", json=payload)

    assert response.status_code == 200
    assert response.json()["nombre"] == "documento.pdf"
