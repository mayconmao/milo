"""Contracts the application depends on. Adapters implement them."""

from typing import Protocol

from milo.domain.classification import Classification
from milo.domain.message import Message


class Classifier(Protocol):
    """Decides the intent of a message."""

    def classify(self, message: Message) -> Classification:
        """Return the classification of a message. Must not raise for valid input."""
        ...