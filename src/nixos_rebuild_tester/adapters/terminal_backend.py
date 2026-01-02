"""Terminal backend implementation for tmux."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from terminal_state.models.config import SessionConfig
from terminal_state.session.terminal import TerminalSession as TSSession

from nixos_rebuild_tester.domain.exceptions import SessionCreationFailed
from nixos_rebuild_tester.domain.value_objects import TerminalDimensions

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import TerminalConfig, TerminalSession


class TmuxTerminalBackend:
    """Tmux-based terminal backend implementation."""

    async def create_session(self, config: TerminalConfig) -> TerminalSession:
        """Create new tmux terminal session.

        Args:
            config: Terminal configuration

        Returns:
            New terminal session

        Raises:
            SessionCreationFailed: If session creation fails
        """
        try:
            session = TmuxTerminalSession(
                width=config.width,
                height=config.height,
            )
            await session._start()
            return session
        except Exception as e:
            raise SessionCreationFailed(f"Failed to create tmux session: {e}") from e

    async def destroy_session(self, session: TerminalSession) -> None:
        """Clean up terminal session.

        Args:
            session: Session to destroy
        """
        if isinstance(session, TmuxTerminalSession):
            await session._cleanup()


class TmuxTerminalSession:
    """Tmux terminal session implementation."""

    def __init__(self, width: int, height: int):
        """Initialize session.

        Args:
            width: Terminal width
            height: Terminal height
        """
        self._width = width
        self._height = height
        self._session: TSSession | None = None
        self._frames: list[str] = []

    async def _start(self) -> None:
        """Start the terminal session."""
        config = SessionConfig(width=self._width, height=self._height)
        self._session = TSSession(config)
        self._session.__enter__()

    async def _cleanup(self) -> None:
        """Clean up the terminal session."""
        if self._session:
            self._session.__exit__(None, None, None)

    async def send_command(self, command: str) -> None:
        """Send command to terminal.

        Args:
            command: Command string to execute
        """
        if not self._session:
            raise RuntimeError("Session not started")

        self._session.send_command(command, record=True)

    async def capture_frame(self) -> str:
        """Capture current terminal state.

        Returns:
            Terminal content as text
        """
        if not self._session:
            raise RuntimeError("Session not started")

        frame = self._session.capture()
        content = frame.content
        self._frames.append(content)
        return content

    async def wait_for_completion(self, timeout: int) -> int:
        """Wait for command completion.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            Exit code (0 for success)

        Raises:
            SessionTimeout: If timeout exceeded
        """
        import asyncio

        if not self._session:
            raise RuntimeError("Session not started")

        try:
            # Wait for output to appear
            if not self._session.expect_text(
                r"(building|activating|copying|warning|error|failed|completed)",
                timeout=timeout,
            ):
                return 124  # Timeout exit code

            # Let output settle
            await asyncio.sleep(2)

            # Capture final state
            final_frame = self._session.capture()
            self._frames.append(final_frame.content)

            # Check for errors
            if "error" in final_frame.content.lower() or "failed" in final_frame.content.lower():
                return 1

            return 0

        except Exception:
            return 1

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
