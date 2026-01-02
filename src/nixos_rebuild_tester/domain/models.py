"""Core domain models with proper Pydantic validation."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from nixos_rebuild_tester.domain.value_objects import Duration, Timestamp


class RebuildAction(str, Enum):
    """Available nixos-rebuild actions."""

    TEST = "test"
    BUILD = "build"
    DRY_BUILD = "dry-build"
    DRY_ACTIVATE = "dry-activate"


class BuildArtifacts(BaseModel):
    """Collection of build output files."""

    model_config = ConfigDict(frozen=True)

    log_file: Path
    cast_file: Path | None = None
    screenshot_file: Path | None = None
    gif_file: Path | None = None

    @field_validator("log_file")
    @classmethod
    def log_must_exist(cls, v: Path) -> Path:
        """Validate that log file exists."""
        if not v.exists():
            raise ValueError(f"Log file must exist: {v}")
        return v

    @computed_field
    @property
    def all_files(self) -> list[Path]:
        """Return list of all artifact files that exist."""
        return [f for f in [self.log_file, self.cast_file, self.screenshot_file, self.gif_file] if f is not None]


class RebuildResult(BaseModel):
    """Immutable result of a rebuild operation."""

    model_config = ConfigDict(frozen=True)

    success: bool
    exit_code: int
    timestamp: Timestamp
    duration: Duration
    action: RebuildAction
    output_dir: Path
    artifacts: BuildArtifacts
    error_message: str | None = None

    @computed_field
    @property
    def metadata_file(self) -> Path:
        """Return path to metadata file."""
        return self.output_dir / "metadata.json"


class RecordingConfig(BaseModel):
    """Configuration for terminal recording."""

    enabled: bool = Field(default=True, description="Enable terminal recording")
    width: Annotated[int, Field(ge=40, le=200)] = Field(default=120, description="Terminal width in characters")
    height: Annotated[int, Field(ge=20, le=100)] = Field(default=40, description="Terminal height in lines")
    export_gif: bool = Field(default=False, description="Export GIF animation of rebuild")
    export_screenshot: bool = Field(default=True, description="Export final terminal screenshot")


class RebuildConfig(BaseModel):
    """Configuration for rebuild behavior."""

    action: RebuildAction = Field(default=RebuildAction.TEST, description="Rebuild action to perform")
    flake_ref: str = Field(default=".#", description="Flake reference to rebuild")
    timeout_seconds: Annotated[int, Field(ge=60)] = Field(default=1800, description="Maximum rebuild time in seconds")
    capture_interval: Annotated[float, Field(ge=0.1)] = Field(
        default=5.0, description="Seconds between frame captures"
    )


class OutputConfig(BaseModel):
    """Configuration for output storage."""

    base_dir: Path = Field(default=Path("./rebuild-logs"), description="Base directory for all rebuild outputs")
    keep_last_n: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description="Keep only the last N builds (None = keep all)"
    )
    timestamp_format: str = Field(default="%Y%m%d-%H%M%S", description="strftime format for directory timestamps")


class Config(BaseModel):
    """Complete configuration for rebuild tester."""

    recording: RecordingConfig = Field(default_factory=RecordingConfig)
    rebuild: RebuildConfig = Field(default_factory=RebuildConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
