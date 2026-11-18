import pytest
from pydantic import ValidationError

from milo.domain.classification import Classification
from milo.domain.intent import Intent


def test_converts_intent_string() -> None:
    classification = Classification(intent="query", classifier="rules", version="1")
    assert classification.intent is Intent.QUERY


def test_rejects_unknown_intent() -> None:
    with pytest.raises(ValidationError):
        Classification(intent="create", classifier="rules", version="1")


def test_requires_classifier_name() -> None:
    with pytest.raises(ValidationError):
        Classification(intent=Intent.QUERY, classifier="", version="1")