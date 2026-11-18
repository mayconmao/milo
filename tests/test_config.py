from pathlib import Path

import pytest
from pydantic import ValidationError

from milo.config import Settings


@pytest.fixture(autouse=True)
def isolate_from_real_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run each test in an empty folder, so the real .env is never read."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_ALLOWED_CHAT_IDS", raising=False)


def test_reads_token_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    assert Settings().telegram_bot_token.get_secret_value() == "123:abc"


def test_token_is_hidden_when_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    assert "123:abc" not in repr(Settings())


def test_token_is_required() -> None:
    with pytest.raises(ValidationError):
        Settings()


def test_parses_comma_separated_chat_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", " 111, 222 ,")
    assert Settings().telegram_allowed_chat_ids == {111, 222}


def test_empty_allowlist_allows_nobody(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
    assert Settings().telegram_allowed_chat_ids == frozenset()


def test_rejects_non_numeric_chat_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "maycon")
    with pytest.raises(ValidationError):
        Settings()


def test_reads_dotenv_file(monkeypatch: pytest.MonkeyPatch) -> None:
    with open(".env", "w") as env_file:
        env_file.write("TELEGRAM_BOT_TOKEN=999:xyz\nTELEGRAM_ALLOWED_CHAT_IDS=42\n")
    settings = Settings()
    assert settings.telegram_bot_token.get_secret_value() == "999:xyz"
    assert settings.telegram_allowed_chat_ids == {42}