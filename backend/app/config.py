from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load backend/.env regardless of process working directory
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "civic_complaints"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    OPENAI_API_KEY: str = ""
    AI_PROVIDER: str = "gemini"

    CORS_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3000"

    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.85
    MAX_UPLOAD_SIZE_MB: int = 5
    MAX_IMAGES_PER_COMPLAINT: int = 5

    AI_SERVICE_URL: str = ""
    BACKEND_URL: str = "http://127.0.0.1:8000"
    REDIS_URL: str = "redis://127.0.0.1:6380"
    QUEUE_SERVICE_URL: str = "http://127.0.0.1:3030"
    COMPLAINT_AI_QUEUE_NAME: str = "complaint-ai"
    INTERNAL_API_KEY: str = "dev-internal-key"
    CLUSTER_MIN_COMPLAINTS: int = 5
    CLUSTER_RADIUS_METERS: int = 500

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "humanizr@localhost"


@lru_cache
def get_settings() -> Settings:
    return Settings()
