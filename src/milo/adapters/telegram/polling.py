"""Long-polling loop: fetch updates, handle them, send the replies."""

import logging
import time
from collections.abc import Callable
from typing import NoReturn, Protocol

import httpx

from milo.adapters.telegram.client import TelegramError, UpdateBatch
from milo.adapters.telegram.models import TelegramUpdate, to_message
from milo.domain.message import Message

logger = logging.getLogger(__name__)

Handler = Callable[[Message], str]


class BotApi(Protocol):
    """What the loop needs from the Telegram client. Tests pass a fake."""

    def get_updates(self, offset: int | None, timeout: int = 30) -> UpdateBatch: ...

    def send_message(self, chat_id: int, text: str) -> None: ...


def process_update(
    update: TelegramUpdate,
    api: BotApi,
    handle: Handler,
    allowed_chat_ids: frozenset[int],
) -> None:
    """Handle one update and reply in the same chat."""
    if update.message is None:
        return
    chat_id = update.message.chat.id
    if chat_id not in allowed_chat_ids:
        # No reply: a stranger must not learn that the bot is alive.
        logger.warning("Ignoring update from chat %s (not allowed)", chat_id)
        return
    message = to_message(update)
    if message is None:
        api.send_message(chat_id, "Por enquanto só entendo mensagens de texto.")
        return
    api.send_message(chat_id, handle(message))


def poll_once(
    api: BotApi,
    handle: Handler,
    allowed_chat_ids: frozenset[int],
    offset: int | None,
) -> int | None:
    """Fetch one batch, handle every update, return the next offset."""
    batch = api.get_updates(offset)
    for update in batch.updates:
        try:
            process_update(update, api, handle, allowed_chat_ids)
        except Exception:
            # One bad update must not stop the bot. It is not retried.
            logger.exception("Failed to handle update %s", update.update_id)
    return batch.next_offset


def run_polling(
    api: BotApi,
    handle: Handler,
    allowed_chat_ids: frozenset[int],
    retry_delay: float = 5.0,
) -> NoReturn:
    """Poll forever. Network errors wait `retry_delay` seconds and try again."""
    offset: int | None = None
    while True:
        try:
            offset = poll_once(api, handle, allowed_chat_ids, offset)
        except (httpx.HTTPError, TelegramError) as error:
            logger.warning("Polling failed (%s); retrying in %ss", error, retry_delay)
            time.sleep(retry_delay)
