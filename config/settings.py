# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    perplexity_api_key: str
    claude_api_key: str
    replicate_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
