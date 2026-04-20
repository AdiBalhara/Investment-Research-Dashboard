from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ird_user:ird_password@localhost:5432/ird_db"

    # JWT Authentication
    JWT_SECRET: str = "supersecretkey_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Embeddings / vector search
    JINA_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # News API
    NEWS_API_KEY: str = ""

    # Financial Modeling Prep
    FMP_API_KEY: str = ""

    # Groq (Llama 3)
    GROQ_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
