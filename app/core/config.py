from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote, unquote

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError(
                "DATABASE_URL is not set. Create .env from .env.example and set your Supabase PostgreSQL URL."
            )
        database_url = self.database_url
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        return self._encode_password(database_url)

    def _encode_password(self, database_url: str) -> str:
        if "://" not in database_url or "@" not in database_url:
            return database_url

        scheme, rest = database_url.split("://", 1)
        userinfo, host_and_path = rest.rsplit("@", 1)
        if ":" not in userinfo:
            return database_url

        username, password = userinfo.split(":", 1)
        encoded_password = quote(unquote(password), safe="")
        return f"{scheme}://{username}:{encoded_password}@{host_and_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
