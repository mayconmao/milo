from datetime import datetime
from zoneinfo import ZoneInfo

from milo.application.ports import Classifier
from milo.domain.classification import Classification
from milo.domain.intent import Intent
from milo.domain.message import Channel, Message


class AlwaysUnknownClassifier:
    """A fake. It never mentions Classifier, yet it satisfies the contract."""

    def classify(self, message: Message) -> Classification:
        return Classification(
            intent=Intent.UNKNOWN, classifier="always_unknown", version="1"
        )


def describe(classifier: Classifier, message: Message) -> str:
    """Code that depends only on the contract, not on any implementation."""
    result = classifier.classify(message)
    return f"{message.text!r} -> {result.intent} ({result.classifier})"


def test_any_object_with_a_matching_classify_method_is_a_classifier() -> None:
    message = Message(
        channel=Channel.CLI,
        external_id="1",
        sender_id="maycon",
        text="bom dia",
        received_at=datetime(2026, 11, 10, 20, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    result = describe(AlwaysUnknownClassifier(), message)
    assert result == "'bom dia' -> unknown (always_unknown)"
