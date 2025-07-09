import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database settings
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "pass")

    # TravelLine API settings
    TRAVELINE_CLIENT_ID: str = os.getenv("TRAVELINE_CLIENT_ID", "api_connection")
    TRAVELINE_CLIENT_SECRET: str = os.getenv("TRAVELINE_CLIENT_SECRET", "DDDDD99999999999")
    TRAVELINE_AUTH_URL: str = "https://partner.tlintegration.com/auth/token"
    TRAVELINE_API_BASE_URL: str = "https://partner.tlintegration.com/api/content"
    
    # Application settings
    APP_NAME: str = "TravelLine Integration API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PROPERTY_ID: str = os.getenv("PROPERTY_ID", "19208")
    
    # Scheduler settings
    SYNC_INTERVAL_MINUTES: int = int(os.getenv("SYNC_INTERVAL_MINUTES", "2"))
    
    
    class Config:
        env_file = ".env"


settings = Settings()
