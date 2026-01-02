"""Application factory for dependency injection."""

from __future__ import annotations

from pathlib import Path

from nixos_rebuild_tester.adapters.terminal import TmuxTerminalAdapter
from nixos_rebuild_tester.container import Container
from nixos_rebuild_tester.domain.models import (
    BuildArtifacts,
    Config,
    RebuildResult,
    RebuildSession,
)
from nixos_rebuild_tester.domain.value_objects import Duration, ErrorMessage, ErrorSource, OutputDirectory, Timestamp


class Application:
    """Application composition root with dependency injection."""

    def __init__(self, config: Config):
        """Initialize application with configuration.

        Args:
            config: Complete application configuration
        """
        self.config = config
        self._container = Container(config)

    async def run_rebuild(self) -> RebuildResult:
        """Execute rebuild with full workflow.

        Returns:
            Rebuild result with all metadata and artifacts

        Note:
            This method never raises exceptions - all errors are captured
            in the RebuildResult with appropriate exit codes.
        """
        # Create rebuild session
        session = RebuildSession.create(self.config.rebuild)

        # Create output directory
        output_dir = self._container.directory_manager().create_for_build(session.session_id)

        try:
            # Start session
            session.start()

            # Execute rebuild
            executor = self._container.rebuild_executor()
            outcome = await executor.execute(
                session,
                width=self.config.recording.width,
                height=self.config.recording.height,
            )

            # Complete session with outcome
            result = session.complete(outcome, output_dir)

        except Exception as e:
            # Handle failures
            error = ErrorMessage(
                content=str(e)[:500],
                source=ErrorSource.EXCEPTION,
            )
            result = session.fail(error, output_dir)

        return result
