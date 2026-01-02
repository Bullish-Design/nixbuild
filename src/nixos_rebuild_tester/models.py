"""Data models for NixOS rebuild tester."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class RebuildAction(str, Enum):
    """Available nixos-rebuild actions."""

    TEST = "test"
    BUILD = "build"
    DRY_BUILD = "dry-build"
    DRY_ACTIVATE = "dry-activate"


class RecordingConfig(BaseModel):
    """Configuration for terminal recording."""

    enabled: bool = Field(default=True, description="Enable terminal recording")
    width: int = Field(default=120, ge=40, le=200, description="Terminal width in characters")
    height: int = Field(default=40, ge=20, le=100, description="Terminal height in lines")
    export_gif: bool = Field(default=False, description="Export GIF animation of rebuild")
    export_screenshot: bool = Field(default=True, description="Export final terminal screenshot")


class RebuildConfig(BaseModel):
    """Configuration for rebuild behavior."""

    action: RebuildAction = Field(default=RebuildAction.TEST, description="Rebuild action to perform")
    flake_ref: str = Field(default=".#", description="Flake reference to rebuild")
    timeout_seconds: int = Field(default=1800, ge=60, description="Maximum rebuild time in seconds")
    capture_interval: float = Field(default=5.0, ge=0.1, description="Seconds between frame captures")


class OutputConfig(BaseModel):
    """Configuration for output storage."""

    base_dir: Path = Field(default=Path("./rebuild-logs"), description="Base directory for all rebuild outputs")
    keep_last_n: int | None = Field(default=None, ge=1, description="Keep only the last N builds (None = keep all)")
    timestamp_format: str = Field(default="%Y%m%d-%H%M%S", description="strftime format for directory timestamps")


class Config(BaseModel):
    """Complete configuration for rebuild tester."""

    recording: RecordingConfig = Field(default_factory=RecordingConfig)
    rebuild: RebuildConfig = Field(default_factory=RebuildConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


class RebuildResult(BaseModel):
    """Result of a rebuild operation."""

    success: bool
    exit_code: int
    timestamp: datetime
    duration_seconds: float
    action: RebuildAction
    output_dir: Path
    log_file: Path
    cast_file: Path | None = None
    gif_file: Path | None = None
    screenshot_file: Path | None = None
    error_message: str | None = None
