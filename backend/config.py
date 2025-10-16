import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@postgres:5432/traveline_db")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # TravelLine API settings
    TRAVELINE_CLIENT_ID: str = os.getenv("TRAVELINE_CLIENT_ID", "api_connection")
    TRAVELINE_CLIENT_SECRET: str = os.getenv("TRAVELINE_CLIENT_SECRET", "D6Ts")
    TRAVELINE_AUTH_URL: str = "https://partner.tlintegration.com/auth/token"
    TRAVELINE_API_BASE_URL: str = "https://partner.tlintegration.com/api/content"
    
    # Application settings
    APP_NAME: str = "TravelLine Integration API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PROPERTY_ID: str = os.getenv("PROPERTY_ID", "19208")
    
    # Scheduler settings
    SYNC_INTERVAL_MINUTES: int = int(os.getenv("SYNC_INTERVAL_MINUTES", "2"))
    
    # Cache settings
    TOKEN_CACHE_KEY: str = "traveline_access_token"
    TOKEN_CACHE_TTL: int = 14 * 60  # 14 minutes (less than 15 min token lifetime)
    
    # MinIO settings
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "traveline")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() == "true"
    
    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_IDS: str = os.getenv("TELEGRAM_ADMIN_IDS", "")
    
    @property
    def admin_ids_list(self) -> list[int]:
        """Возвращает список ID админов как список целых чисел"""
        if not self.TELEGRAM_ADMIN_IDS:
            return []
        try:
            return [int(admin_id.strip()) for admin_id in self.TELEGRAM_ADMIN_IDS.split(",") if admin_id.strip()]
        except ValueError:
            logger.warning("Некорректный формат TELEGRAM_ADMIN_IDS")
            return []
    
    
    class Config:
        env_file = ".env"


settings = Settings()
