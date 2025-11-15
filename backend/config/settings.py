from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="AI Financial Chatbot")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=True)
    environment: str = Field(default="development")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")

    # Database
    database_url: str = Field(default="sqlite:///./financial_chatbot.db")
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)

    # Authentication
    secret_key: str = Field(default="your-secret-key-here-change-this")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)

    # Vector Database
    vector_db_path: str = Field(default="./data/vectordb")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    # File Upload
    upload_dir: str = Field(default="./data/uploads")
    max_upload_size: int = Field(default=10485760)  # 10MB

    # Mock API
    mock_api_delay: float = Field(default=0.5)
    mock_api_failure_rate: float = Field(default=0.05)

    # Business Rules
    daily_transfer_limit: float = Field(default=1000.0)
    per_transaction_limit: float = Field(default=500.0)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./logs/app.log")

    @validator("database_url", pre=True)
    def build_database_url(cls, v: str, values: Dict[str, Any]) -> str:
        if v.startswith("sqlite"):
            # Ensure directory exists for SQLite
            Path("./data").mkdir(exist_ok=True)
        return v

    @validator("upload_dir", "vector_db_path", "log_file", pre=True)
    def create_directories(cls, v: str) -> str:
        path = Path(v)
        if v.endswith(".log"):
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
        return str(path)

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create singleton instance
settings = Settings()
