"""The subset of the Telegram Bot API payload that milo reads.

Telegram sends many more fields. Pydantic ignores the ones not declared here,
so a new field on Telegram's side never breaks milo.
"""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from milo.domain.message import Channel, Message


class TelegramUser(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int


class TelegramChat(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int


class TelegramMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_id: int
    sender: TelegramUser | None = Field(default=None, alias="from")
    chat: TelegramChat
    date: AwareDatetime
    text: str | None = None


class TelegramUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)

    update_id: int
    message: TelegramMessage | None = None


def to_message(update: TelegramUpdate) -> Message | None:
    """Translate a Telegram update into a domain Message.

    Returns None for updates milo does not handle yet: edits, photos, audio,
    stickers, or messages with no sender.
    """
    telegram_message = update.message
    if telegram_message is None or telegram_message.sender is None:
        return None
    if telegram_message.text is None or not telegram_message.text.strip():
        return None

    return Message(
        channel=Channel.TELEGRAM,
        external_id=str(update.update_id),
        sender_id=str(telegram_message.sender.id),
        text=telegram_message.text,
        received_at=telegram_message.date,
    )
