import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "Veda Foundation — Bhakti Charu Swami Archives"
    APP_ENV: Literal["dev", "prod"] = "dev"
    SECRET_KEY: str
    DEBUG: bool = APP_ENV == "dev"
    
    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    
    # S3 Storage
    S3_ENDPOINT_URL: str
    S3_REGION: str
    S3_BUCKET: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_FROM: str
    
    # Security
    SESSION_SECRET: str
    SESSION_LIFETIME_MINUTES: int = 1440  # 24 hours
    OTP_EXPIRE_MINUTES: int = 15
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Upload
    MAX_UPLOAD_MB: int = 1024  # 1GB
    
    # Captcha
    CAPTCHA_MODE: Literal["dev", "hcaptcha", "turnstile"] = "dev"
    HCAPTCHA_SITE_KEY: str = ""
    HCAPTCHA_SECRET_KEY: str = ""
    TURNSTILE_SITE_KEY: str = ""
    TURNSTILE_SECRET_KEY: str = ""
    
    # App URL (for email links)
    APP_URL: str = "http://localhost:8000"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "prod"
    
    @property
    def upload_limit_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024
    
    @property
    def allowed_content_types(self) -> dict[str, list[str]]:
        return {
            "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
            "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4"],
            "video": ["video/mp4", "video/webm", "video/ogg"],
            "pdf": ["application/pdf"],
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create a single instance of settings to be imported
settings = get_settings()
