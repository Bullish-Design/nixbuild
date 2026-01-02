"""Core domain models with proper Pydantic validation."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from nixos_rebuild_tester.domain.value_objects import (
    BuildId,
    Duration,
    ErrorMessage,
    OutputDirectory,
    Timestamp,
)


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


class SessionState(str, Enum):
    """State of a rebuild session."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ExecutionOutcome(BaseModel):
    """Outcome of build execution."""

    model_config = ConfigDict(frozen=True)

    exit_code: int = Field(..., description="Process exit code")
    duration: Duration = Field(..., description="Execution duration")
    frames: list[str] = Field(default_factory=list, description="Captured terminal frames")
    error: ErrorMessage | None = Field(default=None, description="Error if execution failed")

    @property
    def is_success(self) -> bool:
        """Return True if execution succeeded.

        Returns:
            True if exit code is 0
        """
        return self.exit_code == 0


class RebuildSession(BaseModel):
    """Aggregate root representing a rebuild session lifecycle."""

    model_config = ConfigDict(validate_assignment=True)

    session_id: BuildId = Field(..., description="Unique session identifier")
    config: RebuildConfig = Field(..., description="Rebuild configuration")
    started_at: Timestamp = Field(..., description="Session start time")
    state: SessionState = Field(default=SessionState.CREATED, description="Current session state")

    @classmethod
    def create(cls, config: RebuildConfig) -> RebuildSession:
        """Create a new rebuild session.

        Args:
            config: Rebuild configuration

        Returns:
            New RebuildSession instance
        """
        return cls(
            session_id=BuildId.generate(),
            config=config,
            started_at=Timestamp(),
            state=SessionState.CREATED,
        )

    def start(self) -> None:
        """Mark session as running.

        Raises:
            ValueError: If session is not in CREATED state
        """
        if self.state != SessionState.CREATED:
            raise ValueError(f"Cannot start session in state {self.state}")
        self.state = SessionState.RUNNING

    def complete(self, outcome: ExecutionOutcome, output_dir: OutputDirectory) -> RebuildResult:
        """Complete session with execution outcome.

        Args:
            outcome: Execution outcome
            output_dir: Output directory for artifacts

        Returns:
            RebuildResult with all metadata

        Raises:
            ValueError: If session is not in RUNNING state
        """
        if self.state != SessionState.RUNNING:
            raise ValueError(f"Cannot complete session in state {self.state}")

        self.state = SessionState.COMPLETED if outcome.is_success else SessionState.FAILED

        # Convert frames to artifacts (temporary - will be refactored)
        log_file = output_dir.log_file
        if not log_file.exists():
            log_file.touch()

        artifacts = BuildArtifacts(
            log_file=log_file,
            cast_file=output_dir.cast_file if output_dir.cast_file.exists() else None,
            screenshot_file=output_dir.screenshot_file if output_dir.screenshot_file.exists() else None,
            gif_file=output_dir.gif_file if output_dir.gif_file.exists() else None,
        )

        return RebuildResult(
            success=outcome.is_success,
            exit_code=outcome.exit_code,
            timestamp=self.started_at,
            duration=outcome.duration,
            action=self.config.action,
            output_dir=output_dir.path,
            artifacts=artifacts,
            error_message=outcome.error.content if outcome.error else None,
        )

    def fail(self, error: ErrorMessage, output_dir: OutputDirectory) -> RebuildResult:
        """Fail session with error.

        Args:
            error: Error that caused failure
            output_dir: Output directory

        Returns:
            RebuildResult representing failure
        """
        self.state = SessionState.FAILED

        # Create minimal artifacts
        log_file = output_dir.log_file
        if not log_file.exists():
            log_file.touch()

        artifacts = BuildArtifacts(
            log_file=log_file,
            cast_file=None,
            screenshot_file=None,
            gif_file=None,
        )

        return RebuildResult(
            success=False,
            exit_code=255,
            timestamp=self.started_at,
            duration=Duration(seconds=0.0),
            action=self.config.action,
            output_dir=output_dir.path,
            artifacts=artifacts,
            error_message=error.content,
        )
