"""The result of classifying a message."""

from pydantic import BaseModel, ConfigDict, Field

from milo.domain.intent import Intent


class Classification(BaseModel):
    """Which intent a message has, and which classifier decided it."""

    model_config = ConfigDict(frozen=True)

    intent: Intent
    classifier: str = Field(min_length=1)
    version: str = Field(min_length=1)