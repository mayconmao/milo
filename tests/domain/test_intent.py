import pytest

from milo.domain.intent import Intent


def test_can_be_built_from_a_stored_string() -> None:
    assert Intent("record_expense") is Intent.RECORD_EXPENSE


def test_rejects_a_value_outside_the_closed_set() -> None:
    with pytest.raises(ValueError):
        Intent("create")


@pytest.mark.parametrize("intent", [Intent.QUERY, Intent.UNKNOWN])
def test_read_only_intents_do_not_write(intent: Intent) -> None:
    assert intent.writes is False


@pytest.mark.parametrize(
    "intent",
    [
        Intent.RECORD_EXPENSE,
        Intent.RECORD_INCOME,
        Intent.RECORD_DELIVERIES,
        Intent.CREATE_REMINDER,
        Intent.CORRECT_LAST,
        Intent.UNDO_LAST,
    ],
)
def test_other_intents_write(intent: Intent) -> None:
    assert intent.writes is True


def test_every_intent_is_classified_as_read_or_write() -> None:
    read = [intent for intent in Intent if not intent.writes]
    assert read == [Intent.QUERY, Intent.UNKNOWN]
