# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "NegotiatorAI"
    APP_VERSION: str = "0.1.0"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # LLM (Qwen)
    DASHSCOPE_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # Authentication (JWT)
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()