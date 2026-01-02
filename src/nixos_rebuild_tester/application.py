"""Application factory for dependency injection."""

from __future__ import annotations

from pathlib import Path

from nixos_rebuild_tester.adapters.exporters.asciinema import AsciinemaExporter
from nixos_rebuild_tester.adapters.exporters.gif import GifExporter
from nixos_rebuild_tester.adapters.exporters.log import LogExporter
from nixos_rebuild_tester.adapters.exporters.screenshot import ScreenshotExporter
from nixos_rebuild_tester.adapters.filesystem import LocalFileSystem
from nixos_rebuild_tester.adapters.terminal import TmuxTerminalAdapter
from nixos_rebuild_tester.domain.models import (
    BuildArtifacts,
    Config,
    RebuildAction,
    RebuildResult,
)
from nixos_rebuild_tester.domain.value_objects import Duration, Timestamp
from nixos_rebuild_tester.services.executor import BuildExecutor, ExecutionConfig
from nixos_rebuild_tester.services.exporter import ArtifactExportService, ExportConfig
from nixos_rebuild_tester.services.history import BuildHistoryManager
from nixos_rebuild_tester.services.metadata import MetadataManager


class Application:
    """Application composition root with dependency injection."""

    def __init__(self, config: Config):
        """Initialize application with configuration.

        Args:
            config: Complete application configuration
        """
        self.config = config

        # Create adapters
        self.filesystem = LocalFileSystem()

        # Create exporters
        exporters = {
            "log": LogExporter(),
            "cast": AsciinemaExporter(),
            "screenshot": ScreenshotExporter(),
            "gif": GifExporter(),
        }

        # Create services
        self.metadata_manager = MetadataManager()

        export_config = ExportConfig(
            export_cast=config.recording.enabled,
            export_screenshot=config.recording.export_screenshot,
            export_gif=config.recording.export_gif,
            export_log=True,
        )

        self.artifact_service = ArtifactExportService(
            exporters=exporters,
            config=export_config,
        )

        self.history_manager = BuildHistoryManager(
            filesystem=self.filesystem,
            base_dir=config.output.base_dir,
            keep_last_n=config.output.keep_last_n,
        )

    async def run_rebuild(self) -> RebuildResult:
        """Execute rebuild with full workflow.

        Returns:
            Rebuild result with all metadata and artifacts

        Note:
            This method never raises exceptions - all errors are captured
            in the RebuildResult with appropriate exit codes.
        """
        # Create output directory
        output_dir = self.history_manager.create_build_directory()

        try:
            # Create execution config
            exec_config = ExecutionConfig(
                action=self.config.rebuild.action,
                flake_ref=self.config.rebuild.flake_ref,
                timeout_seconds=self.config.rebuild.timeout_seconds,
            )

            # Create terminal session
            with TmuxTerminalAdapter(
                width=self.config.recording.width,
                height=self.config.recording.height,
            ) as terminal:
                # Execute rebuild
                executor = BuildExecutor(exec_config)
                exec_result = await executor.execute(terminal)

                # Export artifacts
                artifacts = await self.artifact_service.export_all(terminal, output_dir)

            # Create result
            result = RebuildResult(
                success=exec_result.exit_code == 0,
                exit_code=exec_result.exit_code,
                timestamp=exec_result.timestamp,
                duration=exec_result.duration,
                action=exec_config.action,
                output_dir=output_dir,
                artifacts=artifacts,
                error_message=exec_result.error_message,
            )

        except Exception as e:
            # Never crash - always return a result
            # Create minimal artifacts with just log file
            log_file = output_dir / "rebuild.log"
            log_file.touch()

            artifacts = BuildArtifacts(
                log_file=log_file,
                cast_file=None,
                screenshot_file=None,
                gif_file=None,
            )

            result = RebuildResult(
                success=False,
                exit_code=255,
                timestamp=Timestamp(),
                duration=Duration(seconds=0.0),
                action=self.config.rebuild.action,
                output_dir=output_dir,
                artifacts=artifacts,
                error_message=f"Application error: {str(e)}",
            )

        # Save metadata
        await self.metadata_manager.save(result)

        # Cleanup old builds
        await self.history_manager.cleanup_old_builds()

        return result
