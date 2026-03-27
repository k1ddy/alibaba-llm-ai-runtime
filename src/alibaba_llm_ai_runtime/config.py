from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "alibaba-llm-ai-runtime"
    environment: str = "dev"
    log_level: str = "INFO"
    session_history_max_messages: int = 12
    knowledge_source_dir: str = "knowledge/source"
    retrieval_top_k: int = 2
    tool_audit_log_path: str = "runtime_data/audit/tool-events.jsonl"
    llm_provider: Literal["stub", "dashscope_openai_compatible"] = "stub"
    llm_model: str = "qwen-plus"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: str | None = None
    llm_timeout_seconds: float = 30.0
    llm_system_prompt: str = (
        "You are the semantic owner for a bounded runtime scaffold. "
        "Reply clearly and do not claim unavailable tools."
    )

    model_config = SettingsConfigDict(
        env_prefix="AI_RUNTIME_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
