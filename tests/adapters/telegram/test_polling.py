from datetime import UTC, datetime
from typing import Any

from milo.adapters.telegram.client import UpdateBatch
from milo.adapters.telegram.models import TelegramUpdate
from milo.adapters.telegram.polling import poll_once
from milo.domain.message import Message

ALLOWED = frozenset({111})
DATE = int(datetime(2026, 11, 24, 12, 0, tzinfo=UTC).timestamp())


def update(
    update_id: int, chat_id: int = 111, text: str | None = "oi"
) -> TelegramUpdate:
    message: dict[str, Any] = {
        "message_id": 1,
        "from": {"id": chat_id},
        "chat": {"id": chat_id},
        "date": DATE,
    }
    if text is not None:
        message["text"] = text
    return TelegramUpdate.model_validate({"update_id": update_id, "message": message})


class FakeApi:
    def __init__(self, updates: list[TelegramUpdate], next_offset: int) -> None:
        self.batch = UpdateBatch(updates, next_offset)
        self.offsets: list[int | None] = []
        self.sent: list[tuple[int, str]] = []

    def get_updates(self, offset: int | None, timeout: int = 30) -> UpdateBatch:
        self.offsets.append(offset)
        return self.batch

    def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


def echo(message: Message) -> str:
    return f"eco: {message.text}"


def test_replies_in_the_same_chat_and_returns_next_offset() -> None:
    api = FakeApi([update(10)], next_offset=11)

    next_offset = poll_once(api, echo, ALLOWED, offset=None)

    assert api.sent == [(111, "eco: oi")]
    assert next_offset == 11


def test_passes_the_offset_to_get_updates() -> None:
    api = FakeApi([], next_offset=42)

    poll_once(api, echo, ALLOWED, offset=42)

    assert api.offsets == [42]


def test_ignores_chats_outside_the_allowlist_without_replying() -> None:
    api = FakeApi([update(10, chat_id=999)], next_offset=11)

    poll_once(api, echo, ALLOWED, offset=None)

    assert api.sent == []


def test_explains_when_the_message_has_no_text() -> None:
    api = FakeApi([update(10, text=None)], next_offset=11)

    poll_once(api, echo, ALLOWED, offset=None)

    assert api.sent == [(111, "Por enquanto só entendo mensagens de texto.")]


def test_a_failing_update_does_not_stop_the_batch() -> None:
    def explode_on_boom(message: Message) -> str:
        if message.text == "boom":
            raise RuntimeError("bug")
        return "ok"

    api = FakeApi([update(10, text="boom"), update(11)], next_offset=12)

    next_offset = poll_once(api, explode_on_boom, ALLOWED, offset=None)

    assert api.sent == [(111, "ok")]
    assert next_offset == 12
