"""Manages terminal session lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.exceptions import SessionCreationFailed
from nixos_rebuild_tester.domain.value_objects import TerminalDimensions

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildConfig
    from nixos_rebuild_tester.domain.protocols import TerminalBackend, TerminalSession


class SessionManager:
    """Manages terminal session lifecycle.

    Responsible for creating and cleaning up terminal sessions
    for rebuild operations.
    """

    def __init__(self, backend: TerminalBackend):
        """Initialize session manager.

        Args:
            backend: Terminal backend implementation
        """
        self._backend = backend

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

            # Create config object that implements TerminalConfig protocol
            class _TerminalConfig:
                def __init__(self, dims: TerminalDimensions):
                    self._dims = dims

                @property
                def width(self) -> int:
                    return self._dims.width

                @property
                def height(self) -> int:
                    return self._dims.height

            terminal_config = _TerminalConfig(dimensions)
            session = await self._backend.create_session(terminal_config)
            return session

        except Exception as e:
            raise SessionCreationFailed(f"Failed to create terminal session: {e}") from e

    async def cleanup(self, session: TerminalSession) -> None:
        """Clean up terminal session.

        Args:
            session: Session to clean up
        """
        try:
            await self._backend.destroy_session(session)
        except Exception:
            # Log but don't raise - cleanup is best effort
            pass
