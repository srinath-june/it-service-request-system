import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "IT Service Request Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./it_service_system.db"

    # Default SLA Hours Configuration per Priority
    SLA_CRITICAL_HOURS: int = 4
    SLA_HIGH_HOURS: int = 8
    SLA_MEDIUM_HOURS: int = 24
    SLA_LOW_HOURS: int = 48

    # SLA Breached warning threshold (percentage of time elapsed before showing warning)
    SLA_WARNING_THRESHOLD_PERCENT: float = 75.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
