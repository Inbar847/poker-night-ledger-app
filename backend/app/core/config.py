from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://poker_user:poker_pass@localhost:5432/poker_ledger"
    secret_key: str  # Required — set via SECRET_KEY env var or .env file
    debug: bool = False

    # CORS — comma-separated list of allowed origins (e.g. "http://localhost:8081,https://myapp.com")
    allowed_origins: str = ""

    # JWT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


settings = Settings()
