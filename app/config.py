from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    # Database
    database_url: str = "sqlite:///./erp.db"

    # API
    rate_limit_per_minute: int = 30
    log_level: str = "INFO"


settings = Settings()
