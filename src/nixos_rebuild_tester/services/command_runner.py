# src/nixos_rebuild_tester/services/command_runner.py
"""Builds and executes rebuild commands."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.error_detector import ErrorDetector
from nixos_rebuild_tester.domain.exceptions import ExecutionTimeout
from nixos_rebuild_tester.domain.value_objects import Duration

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import ExecutionOutcome, RebuildConfig
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class CommandRunner:
    """Builds and executes rebuild commands.

    Responsible for building command strings and executing them,
    detecting errors in the output.
    """

    def __init__(self, error_detector: ErrorDetector | None = None):
        """Initialize command runner.

        Args:
            error_detector: Error detector for extracting error messages
        """
        self._error_detector = error_detector or ErrorDetector()

    async def run_rebuild(
        self,
        session: TerminalSession,
        config: RebuildConfig,
    ) -> ExecutionOutcome:
        """Run rebuild command in session.

        Args:
            session: Terminal session
            config: Rebuild configuration

        Returns:
            Execution outcome with results

        Raises:
            ExecutionTimeout: If command times out
        """
        from nixos_rebuild_tester.domain.models import ExecutionOutcome

        start_time = time.time()

        # Build command
        command = self._build_command(config)

        # Send command
        await session.send_command(command)

        # Wait for completion
        try:
            exit_code = await session.wait_for_completion(config.timeout_seconds)
        except Exception as e:
            raise ExecutionTimeout(f"Command timed out after {config.timeout_seconds}s") from e

        # Calculate duration
        duration = Duration(seconds=time.time() - start_time)

        # Get frames
        frames = session.frames

        # Detect errors
        error = None
        if exit_code != 0:
            error = self._error_detector.extract_best_error(
                exit_code=exit_code,
                frames=frames,
            )

        return ExecutionOutcome(
            exit_code=exit_code,
            duration=duration,
            frames=frames,
            error=error,
        )

    def _build_command(self, config: RebuildConfig) -> str:
        """Build nixos-rebuild command string.

        Args:
            config: Rebuild configuration

        Returns:
            Complete command string
        """
        parts = [
            "sudo",
            "nixos-rebuild",
            config.action.value,
            "--flake",
            config.flake_ref,
        ]

        # Add --no-write-lock-file for remote flakes
        if self._is_remote_flake(config.flake_ref):
            parts.append("--refresh")
            parts.append("--no-write-lock-file")

        return " ".join(parts)

    def _is_remote_flake(self, flake_ref: str) -> bool:
        """Check if flake reference is remote.

        Args:
            flake_ref: Flake reference string

        Returns:
            True if flake is remote (github:, git+https:, etc.)
        """
        remote_prefixes = (
            "github:",
            "gitlab:",
            "git+https:",
            "git+ssh:",
            "https:",
            "tarball+https:",
        )
        return flake_ref.startswith(remote_prefixes)
