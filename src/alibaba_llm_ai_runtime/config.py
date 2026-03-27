from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "alibaba-llm-ai-runtime"
    environment: str = "dev"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="AI_RUNTIME_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
