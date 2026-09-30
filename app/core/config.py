from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "validacion-pdf"
    app_version: str = "1.0.0"
    pdf_max_size_mb: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
