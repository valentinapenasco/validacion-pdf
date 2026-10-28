from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "validacion-pdf"
    pdf_max_size_mb: int = 5
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    consul_enabled: bool = False
    consul_http_addr: str = "http://consul:8500"
    consul_http_token_file: str | None = None
    consul_service_address: str | None = None
    consul_service_port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
