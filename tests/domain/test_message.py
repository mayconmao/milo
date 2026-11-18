from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from milo.domain.message import Channel, Message

SAO_PAULO = ZoneInfo("America/Sao_Paulo")
UTC = ZoneInfo("UTC")


def make_message(**overrides: Any) -> Message:
    """Build a valid Message; tests change only the field they care about."""
    data: dict[str, Any] = {
        "channel": Channel.CLI,
        "external_id": "1",
        "sender_id": "maycon",
        "text": "combustivel entregas 30",
        "received_at": datetime(2026, 11, 5, 23, 30, tzinfo=SAO_PAULO),
    }
    data.update(overrides)
    return Message(**data)


def test_valid_message_keeps_its_fields() -> None:
    message = make_message()
    assert message.text == "combustivel entregas 30"
    assert message.channel is Channel.CLI


def test_strips_surrounding_whitespace() -> None:
    assert make_message(text="  uber 27 \n").text == "uber 27"


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_rejects_empty_text(text: str) -> None:
    with pytest.raises(ValidationError):
        make_message(text=text)


def test_rejects_text_over_the_telegram_limit() -> None:
    with pytest.raises(ValidationError):
        make_message(text="a" * 4097)


def test_converts_a_known_channel_string() -> None:
    assert make_message(channel="telegram").channel is Channel.TELEGRAM


def test_rejects_an_unknown_channel() -> None:
    with pytest.raises(ValidationError):
        make_message(channel="whatsapp")


def test_rejects_a_datetime_without_timezone() -> None:
    with pytest.raises(ValidationError):
        make_message(received_at=datetime(2026, 11, 5, 23, 30))


def test_same_instant_is_a_different_day_in_utc() -> None:
    # 23:30 on Nov 5 in São Paulo is already Nov 6 in UTC.
    received_at = make_message().received_at
    assert received_at.astimezone(SAO_PAULO).day == 5
    assert received_at.astimezone(UTC).day == 6


def test_is_immutable() -> None:
    message = make_message()
    with pytest.raises(ValidationError):
        message.text = "changed"  # type: ignore[misc]


def test_error_lists_every_invalid_field() -> None:
    with pytest.raises(ValidationError) as error:
        make_message(text="", channel="whatsapp")
    invalid_fields = {e["loc"][0] for e in error.value.errors()}
    assert invalid_fields == {"text", "channel"}
