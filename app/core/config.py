"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fact Knowledge Layer"
    app_version: str = "1.0.0"
    
    # LLM Settings
    llm_provider: str = "demo"  # 'demo', 'anthropic', 'openai', 'gemini'
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    llm_model: str = "claude-3-5-sonnet-20241022"
    
    # Embedding Settings
    embedding_provider: str = "sentence-transformers"  # 'sentence-transformers' or 'tfidf'
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Storage & Paths
    database_url: str = "sqlite:///./data/fact_layer.db"
    data_dir: Path = Path("./data")
    uploads_dir: Path = Path("./data/uploads")
    
    # Comparison Engine Parameters
    similarity_threshold: float = 0.60
    numeric_tolerance: float = 0.015  # 1.5% relative tolerance for financial rounding
    
    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
