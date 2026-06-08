from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "admin"


settings = Settings()
    # app/config/config.py

from pydantic_settings import BaseSettings
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
    # OOP CONCEPT: INNER CLASS (Meta/Config class)
    # -------------------------------------------------------
    # This inner class tells Pydantic WHERE to read the values from.
    # It's a class defined inside another class — called a nested class.
    # -------------------------------------------------------
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# -------------------------------------------------------
# lru_cache = "only create Settings object ONCE"
# Every time get_settings() is called anywhere in the app,
# it returns the same object instead of re-reading .env each time.
# This is called the Singleton pattern — one instance shared everywhere.
# -------------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Shortcut — import this directly anywhere you need settings
settings = get_settings()