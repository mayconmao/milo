from datetime import UTC, datetime

from milo.adapters.always_unknown import AlwaysUnknownClassifier
from milo.application.ports import Classifier
from milo.domain.intent import Intent
from milo.domain.message import Channel, Message


def test_classifies_everything_as_unknown() -> None:
    classifier: Classifier = AlwaysUnknownClassifier()
    message = Message(
        channel=Channel.TELEGRAM,
        external_id="1",
        sender_id="111",
        text="entregas 160",
        received_at=datetime(2026, 11, 24, 12, 0, tzinfo=UTC),
    )

    classification = classifier.classify(message)

    assert classification.intent is Intent.UNKNOWN
    assert classification.classifier == "always_unknown"
