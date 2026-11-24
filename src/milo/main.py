"""Composition root: builds the concrete objects and starts milo."""

import logging

import httpx

from milo.adapters.always_unknown import AlwaysUnknownClassifier
from milo.adapters.telegram.client import TelegramClient
from milo.adapters.telegram.polling import run_polling
from milo.application.handle_message import HandleMessage
from milo.config import Settings

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    # httpx logs every request URL at INFO, and the URL contains the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = Settings()
    if not settings.telegram_allowed_chat_ids:
        logger.warning("TELEGRAM_ALLOWED_CHAT_IDS is empty: every chat is ignored")

    handle_message = HandleMessage(AlwaysUnknownClassifier())

    with httpx.Client() as http:
        client = TelegramClient(settings.telegram_bot_token, http)
        logger.info("milo is running. Press Ctrl+C to stop.")
        try:
            run_polling(
                client, handle_message.execute, settings.telegram_allowed_chat_ids
            )
        except KeyboardInterrupt:
            logger.info("milo stopped")
