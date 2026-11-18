"""What the user wants to do with a message."""

from enum import StrEnum


class Intent(StrEnum):
    """Closed set of intents. The code reacts differently to each one."""

    RECORD_EXPENSE = "record_expense"
    RECORD_INCOME = "record_income"
    RECORD_DELIVERIES = "record_deliveries"
    CREATE_REMINDER = "create_reminder"
    QUERY = "query"
    CORRECT_LAST = "correct_last"
    UNDO_LAST = "undo_last"
    UNKNOWN = "unknown"

    @property
    def writes(self) -> bool:
        """True if handling this intent changes stored data."""
        return self not in _READ_ONLY_INTENTS


_READ_ONLY_INTENTS = frozenset({Intent.QUERY, Intent.UNKNOWN})
