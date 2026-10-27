"""Configuração central do projeto, carregada de variáveis de ambiente / .env.

Import típico:
    from core.settings import settings
    settings.llm_model
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    ollama_host: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:3b-instruct"
    embed_model: str = "bge-m3"
    embed_query_prefix: str = ""
    embed_doc_prefix: str = ""
    ollama_keep_alive: str = "30m"
    embed_num_gpu: int = 0
    llm_num_gpu: int = -1
    llm_temperature: float = 0.15

    llm_provider: str = "auto"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    scrape_min_delay: float = 1.0
    scrape_max_delay: float = 2.0

    chroma_collection: str = "wiki_rag"
    chroma_space: str = "cosine"

    rag_top_k: int = 5
    rag_min_similarity: float = 0.3
    rag_query_rewrite: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "*"
    api_key: str = ""
    rate_limit_per_minute: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.api_cors_origins.strip()
        if raw == "*" or not raw:
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
