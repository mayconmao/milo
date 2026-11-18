from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from milo.adapters.telegram.models import TelegramUpdate, to_message
from milo.domain.message import Channel

SAO_PAULO = ZoneInfo("America/Sao_Paulo")

# 2026-11-18 22:30 in São Paulo, which is already Nov 19 in UTC.
LATE_EVENING = 1795051800


def make_update(**message_overrides: Any) -> dict[str, Any]:
    """A private text message, shaped like the real Bot API JSON."""
    message: dict[str, Any] = {
        "message_id": 7,
        "from": {"id": 111, "is_bot": False, "first_name": "Maycon"},
        "chat": {"id": 111, "type": "private", "first_name": "Maycon"},
        "date": LATE_EVENING,
        "text": "combustivel entregas 30",
    }
    message.update(message_overrides)
    return {"update_id": 900, "message": message}


def parse(payload: dict[str, Any]) -> TelegramUpdate:
    return TelegramUpdate.model_validate(payload)


def test_converts_a_text_message() -> None:
    message = to_message(parse(make_update()))
    assert message is not None
    assert message.channel is Channel.TELEGRAM
    assert message.text == "combustivel entregas 30"
    assert message.sender_id == "111"


def test_uses_update_id_as_external_id() -> None:
    message = to_message(parse(make_update()))
    assert message is not None
    assert message.external_id == "900"


def test_unix_date_becomes_an_aware_utc_datetime() -> None:
    message = to_message(parse(make_update()))
    assert message is not None
    assert message.received_at == datetime(2026, 11, 19, 1, 30, tzinfo=UTC)
    assert message.received_at.astimezone(SAO_PAULO).day == 18


def test_ignores_unknown_fields() -> None:
    payload = make_update(entities=[{"type": "bold", "offset": 0, "length": 5}])
    assert to_message(parse(payload)) is not None


def test_ignores_an_update_without_a_new_message() -> None:
    edited = {"update_id": 901, "edited_message": make_update()["message"]}
    assert to_message(parse(edited)) is None


@pytest.mark.parametrize("text", [None, "   "])
def test_ignores_a_message_without_usable_text(text: str | None) -> None:
    payload = make_update(text=text, photo=[{"file_id": "abc"}])
    assert to_message(parse(payload)) is None


def test_ignores_a_message_without_sender() -> None:
    assert to_message(parse(make_update(**{"from": None}))) is None


def test_rejects_a_payload_without_update_id() -> None:
    with pytest.raises(ValidationError):
        parse({"message": make_update()["message"]})
