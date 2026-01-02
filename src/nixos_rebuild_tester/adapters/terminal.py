"""Terminal session adapter for terminal-state library."""

from __future__ import annotations

import asyncio
import re
from typing import Any
from uuid import uuid4

from terminal_state import Recording, TerminalSession as TerminalStateSession

from nixos_rebuild_tester.domain.exceptions import SessionTimeout

class TmuxTerminalAdapter:
    """Adapter for terminal-state tmux backend."""

    _exit_marker_prefix = "__nrt_exit_code__"

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
        self._exit_marker: str | None = None

    def __enter__(self) -> TmuxTerminalAdapter:
        """Start terminal session context."""
        self._session = TerminalStateSession.create(width=self._width, height=self._height)
        return self

    def __exit__(self, *args: Any) -> None:
        """Clean up terminal session."""
        if self._session:
            self._session.destroy()
            self._session = None

    async def send_command(self, command: str) -> None:
        """Send command to terminal session with exit marker."""
        if not self._session:
            raise RuntimeError("Session not started - use context manager")

        self._frames = []
        self._recording = None

        marker = f"{self._exit_marker_prefix}{uuid4().hex}"
        self._exit_marker = marker
        marked_command = f"{command}; printf '\\n{marker}%s\\n' $?"

        await asyncio.to_thread(self._session.send_command, marked_command, True)

    async def wait_for_completion(self, timeout: int) -> int:
        """Wait for command completion and return exit code."""
        if not self._session:
            raise RuntimeError("Session not started - use context manager")
        if not self._exit_marker:
            raise RuntimeError("No command sent - call send_command first")

        pattern = rf"{re.escape(self._exit_marker)}(?P<exit_code>\d+)"
        completed = await asyncio.to_thread(
            self._session.expect_text,
            pattern,
            timeout=timeout,
        )

        if not completed:
            raise SessionTimeout(f"Command did not complete within {timeout}s")

        await asyncio.sleep(0.2)
        final_frame = await asyncio.to_thread(self._session.capture)
        self._update_recording(final_frame)

        exit_code = self._extract_exit_code(pattern)
        return exit_code

    async def close(self) -> None:
        """Close the terminal session."""
        if not self._session:
            return
        await asyncio.to_thread(self._session.destroy)
        self._session = None

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

    def _update_recording(self, final_frame: Any) -> None:
        if self._session and self._session.recording:
            self._session.recording.add_frame(final_frame)
            self._recording = self._session.recording
            self._frames = [frame.content for frame in self._session.recording.frames]
        else:
            self._frames = [getattr(final_frame, "content", str(final_frame))]

    def _extract_exit_code(self, pattern: str) -> int:
        for frame in reversed(self._frames):
            match = re.search(pattern, frame)
            if match:
                return int(match.group("exit_code"))
        return 1
