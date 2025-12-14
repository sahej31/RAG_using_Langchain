import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Ollama models (free & local)
    ollama_model: str = Field(default="llama3")
    ollama_embedding_model: str = Field(default="nomic-embed-text")

    # Paths
    base_dir: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    docs_dir: str = os.path.join(base_dir, "data", "docs")
    eval_dir: str = os.path.join(base_dir, "data", "eval")
    vector_store_dir: str = os.path.join(base_dir, "data", "vector_store")

    # SQLite DB for feedback
    db_url: str = "sqlite:///./local_rag.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
