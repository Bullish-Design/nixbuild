"""Application factory for dependency injection."""

from __future__ import annotations

import json

from nixos_rebuild_tester.container import Container
from nixos_rebuild_tester.domain.models import (
    Config,
    RebuildResult,
    RebuildSession,
)
from nixos_rebuild_tester.domain.value_objects import ErrorMessage, ErrorSource


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

        executor = self._container.rebuild_executor()
        terminal_session = None

        try:
            # Start session
            session.start()

            # Execute rebuild
            outcome, terminal_session = await executor.execute(
                session,
                width=self.config.recording.width,
                height=self.config.recording.height,
                capture_interval_seconds=self.config.recording.capture_interval_seconds,
                max_frames=self.config.recording.max_frames,
            )

            # Export artifacts
            export_pipeline = self._container.export_pipeline()
            await export_pipeline.export_all(terminal_session, output_dir)

            # Complete session with outcome
            result = session.complete(outcome, output_dir)

        except Exception as e:
            # Handle failures
            error = ErrorMessage(
                content=str(e)[:500],
                source=ErrorSource.EXCEPTION,
            )
            result = session.fail(error, output_dir)

        finally:
            if terminal_session is not None:
                await executor.cleanup(terminal_session)

        metadata_payload = result.model_dump(mode="json")
        output_dir.metadata_file.write_text(json.dumps(metadata_payload, indent=2))

        return result
