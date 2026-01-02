"""Immutable value objects for the domain."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, computed_field, field_validator


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
    def milliseconds(self) -> int:
        """Return duration in milliseconds."""
        return int(self.seconds * 1000)

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


class BuildId(BaseModel):
    """Unique identifier for a build with timestamp and sequence."""

    model_config = {"frozen": True}

    timestamp: Timestamp
    sequence: int = Field(default=0, ge=0, description="Sequence number for same-second builds")

    @classmethod
    def generate(cls) -> BuildId:
        """Generate a new build ID with current timestamp.

        Returns:
            New BuildId instance
        """
        return cls(timestamp=Timestamp(), sequence=0)

    @computed_field
    @property
    def filesystem_name(self) -> str:
        """Return filesystem-safe name for this build.

        Format: rebuild-YYYYMMDD-HHMMSS or rebuild-YYYYMMDD-HHMMSS-N for sequences.

        Returns:
            Filesystem-safe directory name
        """
        base = f"rebuild-{self.timestamp.filesystem_safe}"
        if self.sequence > 0:
            return f"{base}-{self.sequence}"
        return base


class OutputDirectory(BaseModel):
    """Build output directory with all artifact paths."""

    model_config = {"frozen": True}

    path: Path
    build_id: BuildId

    @field_validator("path")
    @classmethod
    def path_must_be_absolute(cls, v: Path) -> Path:
        """Validate that path is absolute.

        Args:
            v: Path to validate

        Returns:
            Validated absolute path

        Raises:
            ValueError: If path is not absolute
        """
        if not v.is_absolute():
            raise ValueError(f"Output directory must be absolute path: {v}")
        return v

    @computed_field
    @property
    def cast_file(self) -> Path:
        """Return path to asciinema cast file.

        Returns:
            Path to rebuild.cast
        """
        return self.path / "rebuild.cast"

    @computed_field
    @property
    def log_file(self) -> Path:
        """Return path to log file.

        Returns:
            Path to rebuild.log
        """
        return self.path / "rebuild.log"

    @computed_field
    @property
    def screenshot_file(self) -> Path:
        """Return path to screenshot file.

        Returns:
            Path to final.png
        """
        return self.path / "final.png"

    @computed_field
    @property
    def gif_file(self) -> Path:
        """Return path to GIF file.

        Returns:
            Path to rebuild.gif
        """
        return self.path / "rebuild.gif"

    @computed_field
    @property
    def metadata_file(self) -> Path:
        """Return path to metadata file.

        Returns:
            Path to metadata.json
        """
        return self.path / "metadata.json"


class ErrorSource(str, Enum):
    """Source of an error message."""

    STDERR = "stderr"
    FRAME = "frame"
    EXIT_CODE = "exit_code"
    EXCEPTION = "exception"


class ErrorMessage(BaseModel):
    """Error message with source and context."""

    model_config = {"frozen": True}

    content: str = Field(..., min_length=1, max_length=500, description="Error message content")
    source: ErrorSource = Field(..., description="Where the error was detected")
    timestamp: Timestamp | None = Field(default=None, description="When the error occurred")

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        """Validate that content is not just whitespace.

        Args:
            v: Content to validate

        Returns:
            Validated content

        Raises:
            ValueError: If content is empty or whitespace
        """
        if not v.strip():
            raise ValueError("Error message content cannot be empty")
        return v.strip()
