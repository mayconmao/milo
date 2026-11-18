"""Settings loaded from environment variables and the .env file."""

from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Everything milo needs from the outside world to start."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: SecretStr
    telegram_allowed_chat_ids: Annotated[frozenset[int], NoDecode] = frozenset()

    @field_validator("telegram_allowed_chat_ids", mode="before")
    @classmethod
    def split_chat_ids(cls, value: object) -> object:
        """Turn "123, 456" into {123, 456}. An empty value allows nobody."""
        if isinstance(value, str):
            return {part.strip() for part in value.split(",") if part.strip()}
        return value
