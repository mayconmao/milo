import pytest

from milo.domain.intent import Intent


def test_can_be_built_from_a_stored_string() -> None:
    assert Intent("record_expense") is Intent.RECORD_EXPENSE


def test_rejects_a_value_outside_the_closed_set() -> None:
    with pytest.raises(ValueError):
        Intent("create")


def test_record_deliveries_is_no_longer_an_intent() -> None:
    with pytest.raises(ValueError):
        Intent("record_deliveries")


@pytest.mark.parametrize(
    "intent",
    [
        Intent.QUERY,
        Intent.CREATE_REMINDER,
        Intent.OUT_OF_SCOPE,
        Intent.SMALL_TALK,
        Intent.UNKNOWN,
    ],
)
def test_read_only_intents_do_not_write(intent: Intent) -> None:
    assert intent.writes is False


@pytest.mark.parametrize(
    "intent",
    [
        Intent.RECORD_EXPENSE,
        Intent.RECORD_INCOME,
        Intent.CORRECT_LAST,
        Intent.UNDO_LAST,
    ],
)
def test_writing_intents_write(intent: Intent) -> None:
    assert intent.writes is True


def test_every_intent_is_classified_as_read_or_write() -> None:
    writing = {intent for intent in Intent if intent.writes}
    assert writing == {
        Intent.RECORD_EXPENSE,
        Intent.RECORD_INCOME,
        Intent.CORRECT_LAST,
        Intent.UNDO_LAST,
    }
