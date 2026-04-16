import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Gemini API
    GEMINI_API_KEY: str
    
    # Meta Settings
    META_APP_SECRET: str
    META_WEBHOOK_VERIFY_TOKEN: str
    META_ACCESS_TOKEN: str
    META_PHONE_NUMBER_ID: str
    
    # App Settings
    WEBHOOK_URL: str
    LOG_LEVEL: str = "INFO"
    
    # Supabase Data Layer
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    
    # Security
    VERIFY_META_SIGNATURE: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
