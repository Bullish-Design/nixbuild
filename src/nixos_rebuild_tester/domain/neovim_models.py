"""Models for neovim testing."""

from __future__ import annotations

from datetime import timedelta
from enum import Enum

from pydantic import BaseModel, Field


class KeyModifier(str, Enum):
    """Keyboard modifiers."""

    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"


class KeyStroke(BaseModel):
    """Single keyboard input."""

    key: str = Field(description="Key to press")
    modifiers: list[KeyModifier] = Field(default_factory=list)
    delay_after: timedelta = Field(
        default=timedelta(milliseconds=100),
        description="Wait after keystroke",
    )


class NeovimCommand(BaseModel):
    """Neovim command sequence."""

    description: str = Field(description="What this command does")
    keystrokes: list[KeyStroke] = Field(description="Keys to press")
    wait_for_completion: timedelta = Field(
        default=timedelta(seconds=1),
        description="Wait after sequence",
    )


class NeovimTestConfig(BaseModel):
    """Configuration for neovim test."""

    nvim_config_path: str = Field(
        default="~/.config/nvim",
        description="Path to neovim config",
    )
    test_file: str | None = Field(
        default=None,
        description="File to open (None for empty buffer)",
    )
    commands: list[NeovimCommand] = Field(description="Command sequences")
    timeout_seconds: float = Field(default=60.0, description="Test timeout")
    capture_interval: timedelta = Field(
        default=timedelta(milliseconds=500),
        description="Frame capture interval",
    )
