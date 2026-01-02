"""Protocol definitions for dependency injection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildResult


class ITerminalSession(Protocol):
    """Protocol for terminal session backends."""

    async def execute(self, command: str, timeout: int) -> int:
        """Execute command and return exit code."""
        ...

    def capture_frame(self) -> str:
        """Capture current terminal state as text."""
        ...

    @property
    def dimensions(self) -> tuple[int, int]:
        """Return (width, height) of terminal."""
        ...

    @property
    def frames(self) -> list[str]:
        """Return all captured frames."""
        ...


class IArtifactExporter(Protocol):
    """Protocol for exporting specific artifact types."""

    async def export(self, session: ITerminalSession, output_path: Path) -> Path:
        """Export artifact and return created file path."""
        ...


class IMetadataStore(Protocol):
    """Protocol for metadata persistence."""

    async def save(self, result: RebuildResult) -> Path:
        """Save result metadata and return file path."""
        ...

    async def load(self, metadata_file: Path) -> RebuildResult:
        """Load result from metadata file."""
        ...


class IFileSystem(Protocol):
    """Protocol for file system operations."""

    def create_directory(self, path: Path) -> Path:
        """Create directory and return its path."""
        ...

    def list_directories(self, path: Path, pattern: str) -> list[Path]:
        """List directories matching pattern."""
        ...

    def delete_directory(self, path: Path) -> None:
        """Recursively delete directory."""
        ...
