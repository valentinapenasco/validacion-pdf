from typing import Literal

import httpx
from pydantic_settings import BaseSettings

from app.core.consul_config import leer_config_de_consul


class ConexionConsul(BaseSettings):
    """Lo único que llega por el entorno cuando hay Consul: cómo conectarse."""

    consul_enabled: bool = False
    consul_http_addr: str = "http://consul:8500"
    consul_http_token_file: str | None = None

    model_config = {"env_file": ".env", "extra": "ignore"}


class Settings(ConexionConsul):
    app_name: str = "validacion-pdf"
    pdf_max_size_mb: int = 5
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    consul_service_address: str | None = None
    consul_service_port: int = 8000


def cargar_settings(transport: httpx.BaseTransport | None = None) -> Settings:
    """Contrato 1.6.0: con CONSUL_ENABLED, la configuración sale del KV de Consul
    (config/validacion-pdf/) y tiene prioridad sobre el entorno."""
    conexion = ConexionConsul()
    if not conexion.consul_enabled:
        return Settings()
    if not conexion.consul_http_token_file:
        raise ValueError("CONSUL_HTTP_TOKEN_FILE es obligatorio")
    valores = leer_config_de_consul(
        conexion.consul_http_addr,
        conexion.consul_http_token_file,
        "validacion-pdf",
        transport,
    )
    return Settings(**valores)


settings = cargar_settings()
