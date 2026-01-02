"""Canonical terminal session adapter for terminal-state library."""

from __future__ import annotations

import asyncio
import re
from typing import Any
from uuid import uuid4

from terminal_state import Recording, TerminalSession as TerminalStateSession

from nixos_rebuild_tester.domain.exceptions import SessionTimeout
from nixos_rebuild_tester.domain.value_objects import TerminalDimensions


class TerminalStateSessionAdapter:
    """Async adapter for terminal-state sessions with exit marker completion.

    This is the canonical terminal session adapter that provides:
    - Exit marker-based completion detection for reliable exit codes
    - Async interface wrapping synchronous terminal-state operations
    - Frame capture and recording management
    """

    _exit_marker_prefix = "__nrt_exit_code__"

    def __init__(self, session: TerminalStateSession, dimensions: TerminalDimensions):
        """Initialize adapter with terminal-state session.

        Args:
            session: Underlying terminal-state session
            dimensions: Terminal dimensions (width/height)
        """
        self._session = session
        self._dimensions = dimensions
        self._recording: Recording | None = session.recording
        self._exit_marker: str | None = None

    async def send_command(self, command: str) -> None:
        """Send command to terminal session with exit marker.

        Wraps the command with an exit marker to enable reliable exit code detection.

        Args:
            command: Command string to execute
        """
        # Generate unique exit marker for this command
        marker = f"{self._exit_marker_prefix}{uuid4().hex}"
        self._exit_marker = marker

        # Wrap command with exit code marker
        marked_command = f"{command}; printf '\\n{marker}%s\\n' $?"

        # Send command in background thread
        await asyncio.to_thread(self._session.send_command, marked_command, True)

        # Update recording reference
        self._recording = self._session.recording

    async def wait_for_completion(self, timeout: int) -> int:
        """Wait for command completion using exit marker.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            Exit code from the command

        Raises:
            SessionTimeout: If timeout exceeded
            RuntimeError: If no command was sent first
        """
        if not self._exit_marker:
            raise RuntimeError("No command sent - call send_command first")

        # Wait for exit marker to appear in terminal output
        pattern = rf"{re.escape(self._exit_marker)}(?P<exit_code>\d+)"
        completed = await asyncio.to_thread(
            self._session.expect_text,
            pattern,
            timeout=timeout,
        )

        if not completed:
            raise SessionTimeout(f"Command did not complete within {timeout}s")

        # Capture final frame to ensure marker is in recording
        await asyncio.sleep(0.2)
        final_frame = await asyncio.to_thread(self._session.capture)

        # Update recording with final frame
        self._update_recording(final_frame)

        # Extract and return exit code
        return self._extract_exit_code(pattern)

    async def capture_frame(self) -> str:
        """Capture current terminal frame content.

        Returns:
            Current frame content as string
        """
        frame = await asyncio.to_thread(self._session.capture)
        self._recording = self._session.recording
        return frame.content

    @property
    def dimensions(self) -> TerminalDimensions:
        """Return terminal dimensions."""
        return self._dimensions

    @property
    def frames(self) -> list[str]:
        """Return all captured frames.

        Returns:
            List of frame content strings
        """
        if self._recording and self._recording.frames:
            return [frame.content for frame in self._recording.frames]
        return []

    @property
    def recording(self) -> Recording | None:
        """Return terminal recording.

        Returns:
            Recording object or None if no recording
        """
        return self._recording

    async def close(self) -> None:
        """Close and destroy the terminal session."""
        await asyncio.to_thread(self._session.destroy)

    def _update_recording(self, final_frame: Any) -> None:
        """Update recording with final frame.

        Args:
            final_frame: Frame to add to recording
        """
        if self._session and self._session.recording:
            # Recording is already updated by terminal-state
            self._recording = self._session.recording
        elif hasattr(final_frame, "content"):
            # Fallback: recording may not be available
            pass

    def _extract_exit_code(self, pattern: str) -> int:
        """Extract exit code from frames using pattern.

        Args:
            pattern: Regex pattern to match exit code

        Returns:
            Extracted exit code, or 1 if not found
        """
        # Search frames in reverse order (most recent first)
        for frame in reversed(self.frames):
            match = re.search(pattern, frame)
            if match:
                return int(match.group("exit_code"))

        # If marker not found, return error code
        return 1
