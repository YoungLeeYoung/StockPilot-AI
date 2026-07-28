from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "StockPilot AI API"
    app_env: str = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = (
        "postgresql+psycopg://"
        "stockpilot:stockpilot_dev_password@localhost:5432/stockpilot"
    )
    redis_url: str = "redis://localhost:6379/0"
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    pdf_max_file_size_mb: int = 20
    pdf_max_pages: int = 300
    pdf_max_text_chars: int = 200_000

    @computed_field
    @property
    def frontend_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
