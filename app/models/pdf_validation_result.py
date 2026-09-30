from dataclasses import dataclass


@dataclass
class PdfValidationResult:
    valido: bool
    nombre: str
    tamano_bytes: int
