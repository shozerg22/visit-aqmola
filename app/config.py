from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional

class Settings(BaseSettings):
    # Строка подключения БД может быть невалидным URL для pydantic AnyUrl (например, sqlite DSN без host),
    # поэтому храним как обычную строку без валидации.
    DATABASE_URL: Optional[str] = None
    ADMIN_TOKEN: Optional[str] = None
    JWT_SECRET: str = "dev-secret"
    JWT_TTL_SECONDS: int = 3600
    RAG_SEARCH_MODE: str = "simple"
    RAG_DATA_DIR: str = "data/rag"
    RAG_BACKEND: str = "files"  # files | pgvector
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    PGVECTOR_DIM: int = 1536
    MAX_RAG_DOC_CHARS: int = 8000
    RATE_LIMIT_WINDOW_SEC: int = 60
    RATE_LIMIT_MAX_REQUESTS: int = 120
    METRICS_ENABLED: int = 1

    @validator("RAG_SEARCH_MODE")
    def _mode_v(cls, v):
        v = v.lower()
        if v not in {"simple","tfidf","embeddings"}:
            return "simple"
        return v

    @validator("RAG_BACKEND")
    def _backend_v(cls, v):
        v = v.lower()
        if v not in {"files","pgvector"}:
            return "files"
        return v

settings = Settings()
