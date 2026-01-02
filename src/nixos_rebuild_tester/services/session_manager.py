"""Manages terminal session lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from terminal_state import TerminalSession as TerminalStateSession

from nixos_rebuild_tester.adapters.terminal_state_session import TerminalStateSessionAdapter
from nixos_rebuild_tester.domain.exceptions import SessionCreationFailed
from nixos_rebuild_tester.domain.value_objects import TerminalDimensions

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildConfig
    from nixos_rebuild_tester.domain.protocols import TerminalSession


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
