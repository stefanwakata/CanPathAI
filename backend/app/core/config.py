"""Application configuration via environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    max_tokens: int = 2048

    # Databases
    database_url: str = "postgresql+psycopg2://canpath:canpath@localhost:5432/canpath"
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection: str = "canpath_docs"

    # Embeddings: "minilm" (sentence-transformers all-MiniLM-L6-v2) or "chroma-onnx"
    embedding_backend: str = "minilm"

    # API
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    session_ttl_minutes: int = 120
    max_history_messages: int = 20

    # Ingestion
    data_raw_dir: str = "./data/raw"
    data_seed_dir: str = "./data/seed"
    ingest_use_seed_fallback: bool = True
    http_timeout_seconds: int = 120

    # Evaluation
    ragas_results_path: str = "./data/ragas_results.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
