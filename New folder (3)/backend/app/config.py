"""Crestal Backend Configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    APP_NAME: str = "Crestal API"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "sqlite:///./crestal.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Gemini AI
    GEMINI_API_KEY: str = ""
    
    # OTP
    OTP_EXPIRY_MINUTES: int = 10
    
    # Simulation
    SESSION_TIMEOUT_MINUTES: int = 30
    COOLDOWN_HOURS_BEGINNER: int = 48
    COOLDOWN_HOURS_INTERMEDIATE: int = 72
    COOLDOWN_HOURS_ADVANCED: int = 120
    COOLDOWN_HOURS_EXPERT: int = 168
    
    # Pass thresholds
    KNOWLEDGE_PASS_THRESHOLD: float = 80.0
    MINI_TASK_PASS_THRESHOLD: float = 70.0
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
