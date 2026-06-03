from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Sensitive â€” required, no defaults (INV-05)
    DATABASE_URL: str
    SECRET_KEY: str

    # JWT (ADR-0005: refresh token via httpOnly cookie)
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Application
    APP_NAME: str = "ManutenÃ§Ã£o"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Celery / Redis
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str | None = None
    MINIO_SECRET_KEY: str | None = None
    MINIO_BUCKET: str = "manutencao"
    MINIO_SECURE: bool = False

    # Attachments (P11)
    ATTACHMENT_ALLOWED_MIME_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "video/mp4",
        "video/quicktime",
    ]
    ATTACHMENT_MAX_IMAGE_BYTES: int = 10 * 1024 * 1024   # 10 MB
    ATTACHMENT_MAX_VIDEO_BYTES: int = 200 * 1024 * 1024  # 200 MB
    ATTACHMENT_UPLOAD_EXPIRE_SECONDS: int = 300   # 5 min
    ATTACHMENT_DOWNLOAD_EXPIRE_SECONDS: int = 3600  # 60 min

    # Email (SMTP)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "noreply@manutencao.local"


settings = Settings()

