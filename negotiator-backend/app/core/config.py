# app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "NegotiatorAI"
    APP_VERSION: str = "0.1.0"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    DASHSCOPE_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    ADMIN_EMAIL: str = "admin@negotiator-ai.com"
    ADMIN_PASSWORD: str = ""
    ADMIN_NAME: str = "Administrator"

    ADMIN_REGISTRATION_ENABLED: bool = True
    ADMIN_REGISTRATION_CODE: str = ""

    # Background cleanup: mark ongoing sessions as interrupted
    # if there is no activity for SESSION_TIMEOUT_MINUTES minutes.
    SESSION_CLEANUP_INTERVAL_SECONDS: int = 300
    SESSION_TIMEOUT_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()