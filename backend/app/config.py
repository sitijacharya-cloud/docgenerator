from pydantic_settings import BaseSettings
from functools import lru_cache
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.3
    max_tokens: int = 1000
    
    storage_path: str = "./storage"
    output_path: str = "./storage/outputs"
    chroma_persist_dir: str = "./storage/chromadb"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()