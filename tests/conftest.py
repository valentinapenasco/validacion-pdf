import fitz
import pytest


def _pdf_cifrado(user_pw: str) -> bytes:
    documento = fitz.open()
    documento.new_page()
    try:
        return documento.tobytes(
            encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=user_pw, owner_pw="duenio"
        )
    finally:
        documento.close()


@pytest.fixture
def pdf_con_contrasena() -> bytes:
    """PDF cifrado con contraseña de usuario: sin ella no se puede abrir."""
    return _pdf_cifrado(user_pw="secreta")


@pytest.fixture
def pdf_solo_con_permisos() -> bytes:
    """PDF cifrado solo con contraseña de dueño (restringe permisos como imprimir o
    copiar): cualquiera lo abre y se lee sin contraseña."""
    return _pdf_cifrado(user_pw="")
