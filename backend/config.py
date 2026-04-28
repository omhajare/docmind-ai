from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache

# Resolve .env relative to this file (backend/.env)
_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    # ─── Environment ─────────────────────────────────────────
    ENVIRONMENT: str = "local"
    APP_VERSION: str = "1.0.0"

    # ─── Database ────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/docmind"

    # ─── CORS ────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173"

    # ─── JWT / Auth ──────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-random-64-char-hex-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    BCRYPT_WORK_FACTOR: int = 12
    PASSWORD_MIN_LENGTH: int = 8
    ADMIN_PASSWORD: str = "admin"

    # ─── LLM ─────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ─── Web Search ──────────────────────────────────────────
    TAVILY_API_KEY: str = ""

    # ─── Supabase (production) ───────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # ─── ChromaDB ────────────────────────────────────────────
    CHROMA_HOST: str = ""
    CHROMA_API_KEY: str = ""
    CHROMA_TENANT: str = ""
    CHROMA_DATABASE: str = ""

    # ─── Email ───────────────────────────────────────────────
    EMAIL_PROVIDER: str = "resend"
    RESEND_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "noreply@yourdomain.com"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # ─── Document Management ─────────────────────────────────
    MAX_PDF_SIZE_MB: int = 10
    MAX_DOCUMENTS_PER_USER: int = 5
    SUGGESTED_QUESTIONS_COUNT: int = 5

    # ─── RAG ─────────────────────────────────────────────────
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5
    WEB_SEARCH_FALLBACK_THRESHOLD: float = 0.65

    # ─── Chat ────────────────────────────────────────────────
    CHAT_CONTEXT_WINDOW: int = 10
    CHAT_HISTORY_LIMIT: int = 10
    MAX_CHAT_QUERY_LENGTH: int = 2000
    SESSION_TITLE_MAX_LENGTH: int = 50
    MAX_SESSIONS_PER_USER: int = 20

    # ─── Confidence ──────────────────────────────────────────
    CONFIDENCE_HIGH_THRESHOLD: float = 0.75
    CONFIDENCE_MEDIUM_THRESHOLD: float = 0.65
    RESEARCH_CONFIDENCE_HIGH: float = 0.70
    RESEARCH_CONFIDENCE_MEDIUM: float = 0.45
    WEB_SEARCH_PENALTY: float = 0.10

    # ─── Deep Research ───────────────────────────────────────
    MAX_RESEARCH_TOPIC_LENGTH: int = 300
    MAX_SUB_QUESTIONS: int = 5
    MAX_REFLECTION_ITERATIONS: int = 3
    RESEARCH_JOB_HISTORY_LIMIT: int = 3
    RESEARCH_JOB_RETENTION_DAYS: int = 7
    STALE_JOB_TIMEOUT_MINUTES: int = 20

    # ─── Rate Limiting ───────────────────────────────────────
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    RATE_LIMIT_AI_REQUESTS_PER_MINUTE: int = 10

    # ─── Pagination ──────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20

    # ─── RAGAS Evaluation ────────────────────────────────────
    EVAL_DATASET_SIZE: int = 10
    EVAL_PASS_THRESHOLD: float = 0.70
    EVAL_BACKEND_URL: str = "http://localhost:8000"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
