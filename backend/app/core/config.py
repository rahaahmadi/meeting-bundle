from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: int = 60

    database_url: str = "sqlite:///./app.db"

    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "noreply@internal.app"


settings = Settings()
