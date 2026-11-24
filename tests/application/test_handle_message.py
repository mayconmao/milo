from datetime import UTC, datetime

from milo.application.handle_message import HandleMessage
from milo.domain.classification import Classification
from milo.domain.intent import Intent
from milo.domain.message import Channel, Message


def make_message(text: str = "combustivel 30") -> Message:
    return Message(
        channel=Channel.TELEGRAM,
        external_id="1",
        sender_id="111",
        text=text,
        received_at=datetime(2026, 11, 24, 12, 0, tzinfo=UTC),
    )


class FakeClassifier:
    """Returns a fixed intent and remembers what it received."""

    def __init__(self, intent: Intent) -> None:
        self.intent = intent
        self.received: list[Message] = []

    def classify(self, message: Message) -> Classification:
        self.received.append(message)
        return Classification(intent=self.intent, classifier="fake", version="1")


def test_passes_the_message_to_the_classifier() -> None:
    classifier = FakeClassifier(Intent.RECORD_EXPENSE)
    message = make_message()

    HandleMessage(classifier).execute(message)

    assert classifier.received == [message]


def test_reply_shows_intent_and_classifier() -> None:
    classifier = FakeClassifier(Intent.RECORD_EXPENSE)

    reply = HandleMessage(classifier).execute(make_message())

    assert reply == "Entendi: record_expense (fake v1)"
