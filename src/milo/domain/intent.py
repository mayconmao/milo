"""What the user wants to do with a message."""

from enum import StrEnum


class Intent(StrEnum):
    """Closed set of v1 intents. The code reacts differently to each one."""

    RECORD_EXPENSE = "record_expense"
    RECORD_INCOME = "record_income"
    QUERY = "query"
    CORRECT_LAST = "correct_last"
    UNDO_LAST = "undo_last"
    CREATE_REMINDER = "create_reminder"
    OUT_OF_SCOPE = "out_of_scope"
    SMALL_TALK = "small_talk"
    UNKNOWN = "unknown"

    @property
    def writes(self) -> bool:
        """True if handling this intent changes stored data."""
        return self in _WRITING_INTENTS


# Allow-list on purpose: a new intent never writes unless it is added here.
# CREATE_REMINDER is recognized in v1 but not supported yet, so it does not write.
_WRITING_INTENTS = frozenset(
    {
        Intent.RECORD_EXPENSE,
        Intent.RECORD_INCOME,
        Intent.CORRECT_LAST,
        Intent.UNDO_LAST,
    }
)
