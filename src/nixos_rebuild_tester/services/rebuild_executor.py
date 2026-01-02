"""Coordinates rebuild execution (application service)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.exceptions import ExecutionTimeout
from nixos_rebuild_tester.services.command_runner import CommandRunner
from nixos_rebuild_tester.services.frame_recorder import FrameRecorder
from nixos_rebuild_tester.services.session_manager import SessionManager

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import ExecutionOutcome, RebuildSession
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class RebuildExecutor:
    """Coordinates rebuild execution.

    Orchestrates session creation, command execution, and frame recording
    to perform a complete rebuild operation.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        command_runner: CommandRunner,
        frame_recorder: FrameRecorder,
    ):
        """Initialize rebuild executor.

        Args:
            session_manager: Session lifecycle manager
            command_runner: Command execution service
            frame_recorder: Frame recording service
        """
        self._session_manager = session_manager
        self._command_runner = command_runner
        self._frame_recorder = frame_recorder

    async def execute(
        self,
        rebuild_session: RebuildSession,
        width: int = 120,
        height: int = 40,
    ) -> tuple[ExecutionOutcome, "TerminalSession"]:
        """Execute rebuild with proper resource management.

        Args:
            rebuild_session: Rebuild session to execute
            width: Terminal width
            height: Terminal height

        Returns:
            Execution outcome with results

        Raises:
            ExecutionTimeout: If execution times out
            SessionCreationFailed: If session creation fails
        """
        # Create terminal session
        terminal_session = await self._session_manager.create_for_rebuild(
            rebuild_session.config,
            width=width,
            height=height,
        )

        try:
            # Create execution task
            execution_task = asyncio.create_task(
                self._command_runner.run_rebuild(
                    terminal_session,
                    rebuild_session.config,
                )
            )

            # Wait for completion
            outcome = await execution_task

            return outcome, terminal_session

        except asyncio.TimeoutError as e:
            execution_task.cancel()
            await self._session_manager.cleanup(terminal_session)
            raise ExecutionTimeout(
                f"Execution timed out after {rebuild_session.config.timeout_seconds}s"
            ) from e

        except Exception:
            await self._session_manager.cleanup(terminal_session)
            raise

    async def cleanup(self, session: "TerminalSession") -> None:
        """Clean up terminal session.

        Args:
            session: Terminal session to clean up
        """
        await self._session_manager.cleanup(session)
