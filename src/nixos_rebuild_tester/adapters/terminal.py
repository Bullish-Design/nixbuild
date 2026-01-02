"""Terminal session adapter for terminal-state library."""

from __future__ import annotations

import asyncio
from typing import Any

from terminal_state import Recording, TerminalSession as TerminalStateSession

from nixos_rebuild_tester.domain.value_objects import TerminalDimensions


class TmuxTerminalAdapter:
    """Adapter for terminal-state tmux backend."""

    def __init__(self, width: int, height: int):
        """Initialize terminal adapter.

        Args:
            width: Terminal width in characters
            height: Terminal height in lines
        """
        self._width = width
        self._height = height
        self._session: TerminalStateSession | None = None
        self._frames: list[str] = []
        self._recording: Recording | None = None

    def __enter__(self) -> TmuxTerminalAdapter:
        """Start terminal session context."""
        self._session = TerminalStateSession.create(width=self._width, height=self._height)
        return self

    def __exit__(self, *args: Any) -> None:
        """Clean up terminal session."""
        if self._session:
            self._session.destroy()

    async def execute(self, command: str, timeout: int) -> int:
        """Execute command with periodic frame capture.

        Args:
            command: Command to execute
            timeout: Maximum execution time in seconds

        Returns:
            Exit code (0 for success, 124 for timeout, 1 for error)
        """
        if not self._session:
            raise RuntimeError("Session not started - use context manager")

        # Send command (record=True adds frame to recording)
        self._session.send_command(command, record=True)

        # Wait for output to appear with timeout
        try:
            if not self._session.expect_text(
                r"(building|activating|copying|warning|error|failed)",
                timeout=timeout,
            ):
                return 124  # Timeout exit code

            # Let output settle
            await asyncio.sleep(2)

            # Capture final state
            final_frame = self._session.capture()
            if self._session.recording:
                self._session.recording.add_frame(final_frame)
                self._recording = self._session.recording

            # Store frames
            if self._session.recording:
                self._frames = [f.content for f in self._session.recording.frames]

            # Check for errors in output
            if "error" in final_frame.content.lower() or "failed" in final_frame.content.lower():
                return 1

            return 0

        except Exception:
            return 1

    def capture_frame(self) -> str:
        """Capture current terminal state.

        Returns:
            Terminal content as text
        """
        if not self._session:
            raise RuntimeError("Session not started")
        return self._session.capture().content

    @property
    def dimensions(self) -> TerminalDimensions:
        """Return terminal dimensions.

        Returns:
            TerminalDimensions object
        """
        return TerminalDimensions(width=self._width, height=self._height)

    @property
    def frames(self) -> list[str]:
        """Return all captured frames.

        Returns:
            List of frame content strings
        """
        return self._frames.copy()

    @property
    def recording(self) -> Recording | None:
        """Return the recording object for export.

        Returns:
            Recording object or None if no recording
        """
        return self._recording
