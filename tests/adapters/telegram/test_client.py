import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from milo.adapters.telegram.client import TelegramClient, TelegramError

TOKEN = "123:secret"

Handler = Callable[[httpx.Request], httpx.Response]


def make_client(handler: Handler) -> TelegramClient:
    """A client whose HTTP calls go to `handler` instead of the network."""
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return TelegramClient(SecretStr(TOKEN), http)


def ok(result: Any) -> httpx.Response:
    return httpx.Response(200, json={"ok": True, "result": result})


def text_update(update_id: int) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {
            "message_id": 1,
            "from": {"id": 111},
            "chat": {"id": 111},
            "date": 1795051800,
            "text": "oi",
        },
    }


def test_get_updates_sends_offset_and_timeout() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return ok([])

    make_client(handler).get_updates(offset=42, timeout=5)

    request = requests[0]
    assert request.url.path == f"/bot{TOKEN}/getUpdates"
    assert json.loads(request.content) == {
        "offset": 42,
        "timeout": 5,
        "allowed_updates": ["message"],
    }


def test_first_call_sends_no_offset() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return ok([])

    make_client(handler).get_updates(offset=None)
    assert "offset" not in json.loads(requests[0].content)


def test_parses_updates_and_computes_next_offset() -> None:
    client = make_client(lambda request: ok([text_update(10), text_update(11)]))
    batch = client.get_updates(offset=None)
    assert [update.update_id for update in batch.updates] == [10, 11]
    assert batch.next_offset == 12


def test_empty_batch_keeps_the_offset() -> None:
    batch = make_client(lambda request: ok([])).get_updates(offset=42)
    assert batch.updates == []
    assert batch.next_offset == 42


def test_skips_a_malformed_update_but_moves_past_it() -> None:
    malformed = {"update_id": 11, "message": {"text": "no chat, no date"}}
    client = make_client(lambda request: ok([text_update(10), malformed]))
    batch = client.get_updates(offset=None)
    assert [update.update_id for update in batch.updates] == [10]
    assert batch.next_offset == 12


def test_send_message_posts_chat_and_text() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return ok({"message_id": 99})

    make_client(handler).send_message(chat_id=111, text="recebi")
    assert requests[0].url.path == f"/bot{TOKEN}/sendMessage"
    assert json.loads(requests[0].content) == {"chat_id": 111, "text": "recebi"}


def test_api_refusal_raises_telegram_error() -> None:
    refusal = {"ok": False, "error_code": 401, "description": "Unauthorized"}
    client = make_client(lambda request: httpx.Response(401, json=refusal))
    with pytest.raises(TelegramError, match="Unauthorized"):
        client.get_updates(offset=None)


def test_non_json_response_raises_telegram_error() -> None:
    client = make_client(lambda request: httpx.Response(502, text="Bad Gateway"))
    with pytest.raises(TelegramError, match="502"):
        client.send_message(chat_id=111, text="oi")


def test_errors_never_contain_the_token() -> None:
    refusal = {"ok": False, "description": "Conflict"}
    client = make_client(lambda request: httpx.Response(409, json=refusal))
    with pytest.raises(TelegramError) as error:
        client.get_updates(offset=None)
    assert TOKEN not in str(error.value)
