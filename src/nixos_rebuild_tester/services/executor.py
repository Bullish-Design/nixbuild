"""Build execution service."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.models import RebuildAction
from nixos_rebuild_tester.domain.value_objects import Duration, Timestamp

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import ITerminalSession


@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for build execution."""

    action: RebuildAction
    flake_ref: str
    timeout_seconds: int
    extra_args: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionResult:
    """Result of build execution."""

    exit_code: int
    timestamp: Timestamp
    duration: Duration
    error_message: str | None = None


class BuildExecutor:
    """Executes NixOS rebuild operations."""

    def __init__(self, config: ExecutionConfig):
        """Initialize executor.

        Args:
            config: Execution configuration
        """
        self._config = config

    async def execute(self, session: ITerminalSession) -> ExecutionResult:
        """Execute rebuild command.

        Args:
            session: Terminal session to execute in

        Returns:
            Execution result with exit code and metadata
        """
        start_time = time.time()
        timestamp = Timestamp()

        command = self._build_command()
        exit_code = await session.execute(command, timeout=self._config.timeout_seconds)

        duration = Duration(seconds=time.time() - start_time)

        # Extract error message if failed
        error_message = None
        if exit_code != 0:
            error_message = self._extract_error_from_frames(session.frames)

        return ExecutionResult(
            exit_code=exit_code,
            timestamp=timestamp,
            duration=duration,
            error_message=error_message,
        )

    def _build_command(self) -> str:
        """Construct nixos-rebuild command.

        Returns:
            Complete command string
        """
        parts = [
            "sudo",
            "nixos-rebuild",
            self._config.action.value,
            "--flake",
            self._config.flake_ref,
        ]
        parts.extend(self._config.extra_args)
        return " ".join(parts)

    def _extract_error_from_frames(self, frames: list[str]) -> str:
        """Extract error message from terminal frames.

        Args:
            frames: List of terminal frame content

        Returns:
            Error message string (truncated to 200 chars)
        """
        if not frames:
            return "Build failed (no output captured)"

        # Search for error pattern in last frame
        content = frames[-1] if frames else ""
        error_pattern = r"error:.*"
        matches = re.findall(error_pattern, content, re.IGNORECASE)

        if matches:
            return matches[-1][:200]

        return "Build failed (see logs for details)"
