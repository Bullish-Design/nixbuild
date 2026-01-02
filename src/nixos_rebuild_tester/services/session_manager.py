"""Manages terminal session lifecycle."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from terminal_state import Recording, TerminalSession as TerminalStateSession

from nixos_rebuild_tester.domain.exceptions import SessionCreationFailed, SessionTimeout
from nixos_rebuild_tester.domain.value_objects import TerminalDimensions

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildConfig
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class TerminalStateSessionAdapter:
    """Async adapter for terminal-state sessions."""

    def __init__(self, session: TerminalStateSession, dimensions: TerminalDimensions):
        self._session = session
        self._dimensions = dimensions
        self._recording: Recording | None = session.recording

    async def send_command(self, command: str) -> None:
        """Send command to terminal session."""
        await asyncio.to_thread(self._session.send_command, command, True)
        self._recording = self._session.recording

    async def capture_frame(self) -> str:
        """Capture current terminal frame content."""
        frame = await asyncio.to_thread(self._session.capture)
        self._recording = self._session.recording
        return frame.content

    async def wait_for_completion(self, timeout: int) -> int:
        """Wait for command completion."""
        wait_for_completion = getattr(self._session, "wait_for_completion", None)
        if callable(wait_for_completion):
            return await asyncio.to_thread(wait_for_completion, timeout=timeout)

        expect_text = getattr(self._session, "expect_text", None)
        if callable(expect_text):
            completed = await asyncio.to_thread(expect_text, r".+", timeout=timeout)
            if not completed:
                raise SessionTimeout(f"Command timed out after {timeout}s")
            return 0

        await asyncio.sleep(timeout)
        return 0

    @property
    def dimensions(self) -> TerminalDimensions:
        """Return terminal dimensions."""
        return self._dimensions

    @property
    def frames(self) -> list[str]:
        """Return captured frames."""
        if self._recording and self._recording.frames:
            return [frame.content for frame in self._recording.frames]
        return []

    @property
    def recording(self) -> Recording | None:
        """Return terminal recording."""
        return self._recording

    async def close(self) -> None:
        """Destroy the underlying terminal session."""
        await asyncio.to_thread(self._session.destroy)


class SessionManager:
    """Manages terminal session lifecycle.

    Responsible for creating and cleaning up terminal sessions
    for rebuild operations.
    """

    def __init__(self) -> None:
        """Initialize session manager."""

    async def create_for_rebuild(
        self,
        config: RebuildConfig,
        width: int = 120,
        height: int = 40,
    ) -> TerminalSession:
        """Create terminal session for rebuild.

        Args:
            config: Rebuild configuration
            width: Terminal width in characters
            height: Terminal height in lines

        Returns:
            New terminal session

        Raises:
            SessionCreationFailed: If session creation fails
        """
        try:
            dimensions = TerminalDimensions(width=width, height=height)
            session = TerminalStateSession.create(width=dimensions.width, height=dimensions.height)
            return TerminalStateSessionAdapter(session, dimensions)

        except Exception as e:
            raise SessionCreationFailed(f"Failed to create terminal session: {e}") from e

    async def cleanup(self, session: TerminalSession) -> None:
        """Clean up terminal session.

        Args:
            session: Session to clean up
        """
        try:
            if isinstance(session, TerminalStateSessionAdapter):
                await session.close()
        except Exception:
            # Log but don't raise - cleanup is best effort
            pass
