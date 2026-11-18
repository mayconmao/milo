"""HTTP client for the Telegram Bot API, using long polling."""

import logging
from typing import Any, NamedTuple

import httpx
from pydantic import SecretStr, ValidationError

from milo.adapters.telegram.models import TelegramUpdate

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org"


class TelegramError(Exception):
    """The Bot API answered, but refused the request."""


class UpdateBatch(NamedTuple):
    """The updates of one getUpdates call and the offset for the next call."""

    updates: list[TelegramUpdate]
    next_offset: int | None


class TelegramClient:
    """The two Bot API methods milo needs: receive updates and send a reply."""

    def __init__(self, token: SecretStr, http: httpx.Client) -> None:
        self._http = http
        self._base_url = f"{API_URL}/bot{token.get_secret_value()}"

    def get_updates(self, offset: int | None, timeout: int = 30) -> UpdateBatch:
        """Wait up to `timeout` seconds for new updates after `offset`."""
        payload: dict[str, Any] = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset

        # Telegram holds the request open up to `timeout` seconds,
        # so the HTTP timeout must be longer than that.
        raw_updates = self._call("getUpdates", payload, timeout=timeout + 10)

        updates: list[TelegramUpdate] = []
        next_offset = offset
        for raw in raw_updates:
            # Advance past every update, valid or not, so a malformed one
            # is not fetched again forever.
            next_offset = int(raw["update_id"]) + 1
            try:
                updates.append(TelegramUpdate.model_validate(raw))
            except ValidationError:
                logger.warning("Skipping malformed update %s", raw["update_id"])
        return UpdateBatch(updates, next_offset)

    def send_message(self, chat_id: int, text: str) -> None:
        """Send a text message to a chat."""
        self._call("sendMessage", {"chat_id": chat_id, "text": text})

    def _call(self, method: str, payload: dict[str, Any], timeout: float = 10) -> Any:
        response = self._http.post(
            f"{self._base_url}/{method}", json=payload, timeout=timeout
        )
        try:
            body = response.json()
        except ValueError as error:
            raise TelegramError(
                f"{method}: HTTP {response.status_code} without a JSON body"
            ) from error
        if not body.get("ok"):
            raise TelegramError(f"{method}: {body.get('description', 'unknown error')}")
        return body["result"]
