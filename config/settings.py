# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    openai_api_key: str
    perplexity_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    replicate_api_key: Optional[str] = None
    suno_api_key: Optional[str] = None

    redis_host: str = "localhost"
    redis_port: str = "6379"
    redis_db: str = "0"

    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_default_region: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"

settings = Settings()
