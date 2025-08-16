# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    openai_api_key: str
    perplexity_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    replicate_api_key: Optional[str] = None
    suno_api_key: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
