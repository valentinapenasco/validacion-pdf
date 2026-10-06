import base64

import pytest

from app.core.exceptions import PdfValidationError
from app.services.validation_service import ValidationService


VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] >>\n"
    b"endobj\n%%EOF"
)


def encode(content: bytes) -> str:
    return base64.b64encode(content).decode("ascii")


def test_validate_accepts_a_valid_pdf():
    result = ValidationService().validate(encode(VALID_PDF), "contrato.pdf")

    assert result.valido is True
    assert result.nombre == "contrato.pdf"
    assert result.tamano_bytes == len(VALID_PDF)


def test_validate_rejects_invalid_base64():
    with pytest.raises(PdfValidationError) as error:
        ValidationService().validate("no-es-base64")

    assert error.value.code == "PDF_INVALID"
    assert error.value.status_code == 422


def test_validate_rejects_empty_content():
    with pytest.raises(PdfValidationError) as error:
        ValidationService().validate(encode(b""))

    assert error.value.code == "PDF_INVALID"
    assert error.value.status_code == 422


def test_validate_rejects_content_that_is_not_a_pdf():
    with pytest.raises(PdfValidationError) as error:
        ValidationService().validate(encode(b"texto plano"))

    assert error.value.code == "PDF_INVALID"
    assert error.value.status_code == 422


def test_validate_rejects_corrupted_pdf():
    corrupted_pdf = b"%PDF-1.4\ncontenido incompleto"

    with pytest.raises(PdfValidationError) as error:
        ValidationService().validate(encode(corrupted_pdf))

    assert error.value.code == "PDF_CORRUPTED"
    assert error.value.status_code == 422


def test_validate_rejects_pdf_that_is_too_large():
    oversized_pdf = b"%PDF-1.4\n" + (b"x" * (6 * 1024 * 1024))

    with pytest.raises(PdfValidationError) as error:
        ValidationService().validate(encode(oversized_pdf))

    assert error.value.code == "PDF_TOO_LARGE"
    assert error.value.status_code == 413
    assert error.value.details["received_size_bytes"] == len(oversized_pdf)


def test_validate_uses_default_name_when_name_is_omitted():
    result = ValidationService().validate(encode(VALID_PDF))

    assert result.nombre == "documento.pdf"
