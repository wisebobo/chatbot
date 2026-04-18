"""
Global configuration management module
Uses Pydantic BaseSettings to read settings from environment variables or a .env file
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """LLM adapter configuration"""
    api_base_url: str = Field(default="http://your-company-ai-platform/v1", alias="LLM_API_BASE_URL")
    api_key: str = Field(default="your-api-key", alias="LLM_API_KEY")
    model_name: str = Field(default="gpt-4o", alias="LLM_MODEL_NAME")
    temperature: float = Field(default=0.0, alias="LLM_TEMPERATURE")
    max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")
    request_timeout: int = Field(default=60, alias="LLM_REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")

    class Config:
        env_file = ".env"
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    """Database settings (PostgreSQL used for checkpointer)"""
    postgres_dsn: str = Field(
        default="postgresql://user:password@localhost:5432/chatbot",
        alias="POSTGRES_DSN",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")

    class Config:
        env_file = ".env"
        extra = "ignore"


class APISettings(BaseSettings):
    """FastAPI service settings"""
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    workers: int = Field(default=4, alias="API_WORKERS")
    reload: bool = Field(default=False, alias="API_RELOAD")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    allowed_origins: List[str] = Field(default=["*"], alias="API_ALLOWED_ORIGINS")
    api_secret_key: str = Field(default="change-me-in-production", alias="API_SECRET_KEY")

    class Config:
        env_file = ".env"
        extra = "ignore"


class ControlMSettings(BaseSettings):
    """Control-M skill settings"""
    base_url: str = Field(default="http://controlm-server/api", alias="CONTROLM_BASE_URL")
    username: str = Field(default="ctm_user", alias="CONTROLM_USERNAME")
    password: str = Field(default="", alias="CONTROLM_PASSWORD")
    verify_ssl: bool = Field(default=True, alias="CONTROLM_VERIFY_SSL")
    request_timeout: int = Field(default=30, alias="CONTROLM_TIMEOUT")

    class Config:
        env_file = ".env"
        extra = "ignore"


class RagSettings(BaseSettings):
    """RAG knowledge base search settings"""
    api_url: str = Field(
        default="http://your-group-ai-platform/rag/search",
        alias="RAG_API_URL",
        description="Group AI Platform RAG API endpoint",
    )
    api_key: str = Field(default="", alias="RAG_API_KEY", description="API authentication key")
    request_timeout: int = Field(default=30, alias="RAG_REQUEST_TIMEOUT")
    default_top_k: int = Field(default=5, alias="RAG_DEFAULT_TOP_K")
    min_relevance_score: float = Field(default=0.7, alias="RAG_MIN_RELEVANCE_SCORE")

    class Config:
        env_file = ".env"
        extra = "ignore"


class WikiSettings(BaseSettings):
    """LLM Wiki knowledge base query settings"""
    api_url: str = Field(
        default="http://your-group-ai-platform/wiki/query",
        alias="WIKI_API_URL",
        description="Group AI Platform Wiki API endpoint",
    )
    api_key: str = Field(default="", alias="WIKI_API_KEY", description="API authentication key")
    request_timeout: int = Field(default=30, alias="WIKI_REQUEST_TIMEOUT")
    exact_match_default: bool = Field(default=False, alias="WIKI_EXACT_MATCH_DEFAULT")
    max_content_length: int = Field(default=5000, alias="WIKI_MAX_CONTENT_LENGTH")

    class Config:
        env_file = ".env"
        extra = "ignore"


class MonitoringSettings(BaseSettings):
    """Monitoring and logging settings"""
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")  # json | text
    enable_prometheus: bool = Field(default=True, alias="ENABLE_PROMETHEUS")
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    trace_enabled: bool = Field(default=False, alias="TRACE_ENABLED")
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")

    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings(BaseSettings):
    """Unified settings entry point"""
    env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="LangGraph Enterprise Agent Platform", alias="APP_NAME")
    debug: bool = Field(default=False, alias="APP_DEBUG")

    llm: LLMSettings = LLMSettings()
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    controlm: ControlMSettings = ControlMSettings()
    rag: RagSettings = RagSettings()
    wiki: WikiSettings = WikiSettings()
    monitoring: MonitoringSettings = MonitoringSettings()

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get the global settings singleton (cached)"""
    return Settings()
