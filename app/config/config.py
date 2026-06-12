from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Personal Learning Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str
    ASYNC_DATABASE_URL: str

    # --- JWT Auth ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------------------------------------
    # FIX: replace inner Config class with model_config
    # extra="ignore" → unknown env vars (POSTGRES_*) silently skipped
    # -------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",              # ← KEY FIX
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()