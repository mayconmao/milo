"""A message received from any channel."""

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

# Telegram's limit for a single text message.
MAX_TEXT_LENGTH = 4096


class Channel(StrEnum):
    """Where a message came from."""

    CLI = "cli"
    TELEGRAM = "telegram"


class Message(BaseModel):
    """A message as received. Immutable: it is never edited after creation."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    channel: Channel
    external_id: str = Field(min_length=1)
    sender_id: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    received_at: AwareDatetime
