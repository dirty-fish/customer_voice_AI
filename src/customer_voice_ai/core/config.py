from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Customer Voice AI"
    environment: str = "local"

    data_dir: Path = Path("data")
    raw_data_dir: Path = Path("data/raw")
    interim_data_dir: Path = Path("data/interim")
    processed_data_dir: Path = Path("data/processed")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/customer_voice_ai"
    openai_api_key: str | None = None

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    classifier_model_dir: Path = Path("artifacts/models/classifier")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()