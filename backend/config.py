import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


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
    
    
    class Config:
        env_file = ".env"


settings = Settings()
