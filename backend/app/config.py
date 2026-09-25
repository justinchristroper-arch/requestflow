from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore", populate_by_name=True
    )
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "requestflow"
    postgres_user: str = "requestflow"
    postgres_password: SecretStr | None = None
    database_url: SecretStr | None = None
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "CORS_ORIGINS"),
    )

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, values: list[str]) -> list[str]:
        for value in values:
            parsed = urlsplit(value)
            if (parsed.scheme not in ("http", "https") or not parsed.hostname or "*" in value
                    or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
                raise ValueError("CORS_ORIGINS must contain explicit HTTP(S) origins without paths or wildcards")
        return list(dict.fromkeys(values))

    def sqlalchemy_url(self) -> URL:
        if self.database_url:
            url = make_url(self.database_url.get_secret_value())
            if url.drivername in ("postgres", "postgresql"):
                url = url.set(drivername="postgresql+psycopg")
            return url
        if not self.postgres_password:
            raise ValueError("POSTGRES_PASSWORD is required when DATABASE_URL is not set")
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @model_validator(mode="after")
    def database_credentials(self):
        if not self.database_url and not self.postgres_password:
            raise ValueError("DATABASE_URL or POSTGRES_PASSWORD must be configured")
        return self


class Settings(DatabaseSettings):
    jwt_secret: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    environment: Literal["development", "test", "production"] = "development"

    @field_validator("jwt_secret")
    @classmethod
    def strong_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if len(secret.encode()) < 32 or secret.startswith("replace-"):
            raise ValueError("JWT_SECRET must be a generated secret of at least 32 bytes")
        return value
