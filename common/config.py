# app/database/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class AppSettings(BaseSettings):
    # Database settings
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # Application settings
    APP_NAME: Optional[str] = None
    DEBUG: Optional[bool] = None
    API_VERSION: Optional[str] = None

    # JWT settings
    JWT_SECRET_KEY: str = "01234567890"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_TTL_MINUTES: int = 30
    
    @property
    def DATABASE_URL_asyncpg(self):
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
    
    @property
    def DATABASE_URL_psycopg(self):
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    def validate(self) -> None:
        """Validate critical configuration settings"""
        if not all([self.POSTGRES_HOST, self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB]):
            raise ValueError("Missing required database configuration")

@lru_cache()
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.validate()
    return settings

