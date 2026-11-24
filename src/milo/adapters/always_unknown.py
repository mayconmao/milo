"""Placeholder classifier, used until the rules-based one exists."""

from milo.domain.classification import Classification
from milo.domain.intent import Intent
from milo.domain.message import Message


class AlwaysUnknownClassifier:
    """Answers UNKNOWN for every message. Lets the pipeline run end to end."""

    NAME = "always_unknown"
    VERSION = "0"

    def classify(self, message: Message) -> Classification:
        return Classification(
            intent=Intent.UNKNOWN, classifier=self.NAME, version=self.VERSION
        )
