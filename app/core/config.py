from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "validacion-pdf"
    pdf_max_size_mb: int = 5
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
