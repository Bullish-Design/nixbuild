"""Dependency injection container."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nixos_rebuild_tester.adapters.filesystem import LocalFileSystem
from nixos_rebuild_tester.domain.error_detector import ErrorDetector
from nixos_rebuild_tester.services.build_cleaner import BuildCleaner
from nixos_rebuild_tester.services.command_runner import CommandRunner
from nixos_rebuild_tester.services.directory_manager import BuildDirectoryManager
from nixos_rebuild_tester.services.export_pipeline import ExportPipeline
from nixos_rebuild_tester.services.exporter_registry import ExporterRegistry
from nixos_rebuild_tester.services.frame_recorder import FrameRecorder
from nixos_rebuild_tester.services.rebuild_executor import RebuildExecutor
from nixos_rebuild_tester.services.retention_policy import RetentionPolicy
from nixos_rebuild_tester.services.session_manager import SessionManager

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import Config
    from nixos_rebuild_tester.domain.protocols import FileSystem


class Container:
    """Dependency injection container.

    Manages creation and lifecycle of all application dependencies.
    """

    def __init__(self, config: Config):
        """Initialize container with configuration.

        Args:
            config: Application configuration
        """
        self._config = config
        self._singletons: dict[str, Any] = {}

    # Adapters (singletons)
    def filesystem(self) -> FileSystem:
        """Get filesystem implementation.

        Returns:
            FileSystem singleton
        """
        if "filesystem" not in self._singletons:
            self._singletons["filesystem"] = LocalFileSystem()
        return self._singletons["filesystem"]


    # Domain Services (factories)
    def error_detector(self) -> ErrorDetector:
        """Get error detector service.

        Returns:
            New ErrorDetector instance
        """
        return ErrorDetector()

    # Execution Services (factories)
    def session_manager(self) -> SessionManager:
        """Get session manager service.

        Returns:
            New SessionManager instance
        """
        return SessionManager()

    def command_runner(self) -> CommandRunner:
        """Get command runner service.

        Returns:
            New CommandRunner instance
        """
        return CommandRunner(self.error_detector())

    def frame_recorder(self) -> FrameRecorder:
        """Get frame recorder service.

        Returns:
            New FrameRecorder instance
        """
        return FrameRecorder()

    def rebuild_executor(self) -> RebuildExecutor:
        """Get rebuild executor service.

        Returns:
            New RebuildExecutor instance
        """
        return RebuildExecutor(
            session_manager=self.session_manager(),
            command_runner=self.command_runner(),
            frame_recorder=self.frame_recorder(),
        )

    # Export Services (factories)
    def exporter_registry(self) -> ExporterRegistry:
        """Get exporter registry.

        Returns:
            New ExporterRegistry instance
        """
        return ExporterRegistry()

    def export_pipeline(self) -> ExportPipeline:
        """Get export pipeline.

        Returns:
            New ExportPipeline instance configured with exporters
        """
        registry = self.exporter_registry()
        exporters = registry.create_exporters(self._config.recording)
        return ExportPipeline(exporters)

    # Storage Services (factories)
    def directory_manager(self) -> BuildDirectoryManager:
        """Get directory manager service.

        Returns:
            New BuildDirectoryManager instance
        """
        return BuildDirectoryManager(
            filesystem=self.filesystem(),
            base_directory=self._config.output.base_dir,
        )

    def retention_policy(self) -> RetentionPolicy:
        """Get retention policy.

        Returns:
            New RetentionPolicy instance
        """
        return RetentionPolicy(keep_last_n=self._config.output.keep_last_n)

