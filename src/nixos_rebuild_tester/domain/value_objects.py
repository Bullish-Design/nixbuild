"""Immutable value objects for the domain."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class Timestamp(BaseModel):
    """Immutable timestamp value object."""

    value: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def iso_format(self) -> str:
        """Return ISO 8601 formatted timestamp."""
        return self.value.isoformat()

    @computed_field
    @property
    def filesystem_safe(self) -> str:
        """Return filesystem-safe timestamp format."""
        return self.value.strftime("%Y%m%d-%H%M%S")


class Duration(BaseModel):
    """Duration in seconds with formatting utilities."""

    seconds: Annotated[float, Field(ge=0)]

    @computed_field
    @property
    def minutes(self) -> float:
        """Return duration in minutes."""
        return self.seconds / 60

    @computed_field
    @property
    def formatted(self) -> str:
        """Return human-readable duration (e.g., '5m30s')."""
        mins = int(self.seconds // 60)
        secs = int(self.seconds % 60)
        if mins > 0:
            return f"{mins}m{secs}s"
        return f"{secs}s"


class TerminalDimensions(BaseModel):
    """Terminal size specification with validation."""

    width: Annotated[int, Field(ge=40, le=200)]
    height: Annotated[int, Field(ge=20, le=100)]
