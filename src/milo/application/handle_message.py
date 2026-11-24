"""Use case: react to one incoming message."""

from milo.application.ports import Classifier
from milo.domain.classification import Classification
from milo.domain.message import Message


class HandleMessage:
    """Classify a message and build the reply text.

    Knows nothing about Telegram: it receives a domain Message and returns
    plain text. Any channel can call it.
    """

    def __init__(self, classifier: Classifier) -> None:
        self._classifier = classifier

    def execute(self, message: Message) -> str:
        classification = self._classifier.classify(message)
        return render_reply(classification)


def render_reply(classification: Classification) -> str:
    """Temporary reply: shows what milo understood, for debugging."""
    return (
        f"Entendi: {classification.intent} "
        f"({classification.classifier} v{classification.version})"
    )
