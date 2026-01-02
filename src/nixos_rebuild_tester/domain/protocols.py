"""Protocol definitions for dependency injection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildResult
    from nixos_rebuild_tester.domain.value_objects import BuildId, TerminalDimensions


class TerminalSession(Protocol):
    """Active terminal session."""

    async def send_command(self, command: str) -> None:
        """Send command to terminal.

        Args:
            command: Command string to execute
        """
        ...

    async def capture_frame(self) -> str:
        """Capture current terminal state.

        Returns:
            Terminal content as text
        """
        ...

    async def wait_for_completion(self, timeout: int) -> int:
        """Wait for command completion.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            Exit code (0 for success)

        Raises:
            SessionTimeout: If timeout exceeded
        """
        ...

    @property
    def dimensions(self) -> TerminalDimensions:
        """Return terminal dimensions.

        Returns:
            TerminalDimensions object
        """
        ...

    @property
    def frames(self) -> list[str]:
        """Return all captured frames.

        Returns:
            List of frame content strings
        """
        ...


class TerminalConfig(Protocol):
    """Configuration for terminal creation."""

    @property
    def width(self) -> int:
        """Terminal width in characters."""
        ...

    @property
    def height(self) -> int:
        """Terminal height in lines."""
        ...


class TerminalBackend(Protocol):
    """Abstract terminal session management."""

    async def create_session(self, config: TerminalConfig) -> TerminalSession:
        """Create new terminal session.

        Args:
            config: Terminal configuration

        Returns:
            New terminal session

        Raises:
            SessionCreationFailed: If session creation fails
        """
        ...

    async def destroy_session(self, session: TerminalSession) -> None:
        """Clean up terminal session.

        Args:
            session: Session to destroy
        """
        ...


class ExportMetadata(Protocol):
    """Metadata for artifact export."""

    @property
    def timestamp(self) -> str:
        """Export timestamp."""
        ...

    @property
    def build_id(self) -> BuildId:
        """Build identifier."""
        ...


class ArtifactReference(Protocol):
    """Reference to exported artifact."""

    @property
    def path(self) -> Path:
        """Path to artifact file."""
        ...

    @property
    def size_bytes(self) -> int:
        """File size in bytes."""
        ...

    @property
    def format(self) -> str:
        """Artifact format (cast, png, gif, log)."""
        ...


class ArtifactExporter(Protocol):
    """Export session data to specific format."""

    async def export(
        self,
        frames: list[str],
        output_path: Path,
        metadata: ExportMetadata,
    ) -> ArtifactReference:
        """Export frames to artifact.

        Args:
            frames: Terminal frames to export
            output_path: Where to write artifact
            metadata: Export metadata

        Returns:
            Reference to created artifact

        Raises:
            ExportFailed: If export fails
        """
        ...


class BuildRepository(Protocol):
    """Persist and retrieve build results."""

    async def save(self, result: RebuildResult) -> None:
        """Save build result.

        Args:
            result: Result to save

        Raises:
            StorageError: If save fails
        """
        ...

    async def find_by_id(self, build_id: BuildId) -> RebuildResult | None:
        """Find build by ID.

        Args:
            build_id: Build identifier

        Returns:
            RebuildResult if found, None otherwise
        """
        ...

    async def find_recent(self, limit: int) -> list[RebuildResult]:
        """Find recent builds.

        Args:
            limit: Maximum number to return

        Returns:
            List of recent build results
        """
        ...

    async def delete(self, build_id: BuildId) -> None:
        """Delete build result.

        Args:
            build_id: Build to delete

        Raises:
            BuildNotFound: If build doesn't exist
        """
        ...


class FileSystem(Protocol):
    """Complete filesystem abstraction."""

    # Directory operations
    async def create_directory(self, path: Path) -> Path:
        """Create directory and parents.

        Args:
            path: Directory to create

        Returns:
            Created directory path

        Raises:
            DirectoryCreationFailed: If creation fails
        """
        ...

    async def delete_directory(self, path: Path) -> None:
        """Recursively delete directory.

        Args:
            path: Directory to delete

        Raises:
            FileSystemError: If deletion fails
        """
        ...

    async def list_directories(self, base: Path, pattern: str) -> list[Path]:
        """List directories matching pattern.

        Args:
            base: Base directory to search
            pattern: Glob pattern

        Returns:
            List of matching directories
        """
        ...

    def directory_exists(self, path: Path) -> bool:
        """Check if directory exists.

        Args:
            path: Directory to check

        Returns:
            True if exists and is directory
        """
        ...

    # File operations
    async def write_text(self, path: Path, content: str) -> None:
        """Write text to file.

        Args:
            path: File path
            content: Text content

        Raises:
            PathNotWritable: If write fails
        """
        ...

    async def read_text(self, path: Path) -> str:
        """Read text from file.

        Args:
            path: File path

        Returns:
            File contents

        Raises:
            PathNotFound: If file doesn't exist
        """
        ...

    async def write_bytes(self, path: Path, content: bytes) -> None:
        """Write bytes to file.

        Args:
            path: File path
            content: Byte content

        Raises:
            PathNotWritable: If write fails
        """
        ...

    async def read_bytes(self, path: Path) -> bytes:
        """Read bytes from file.

        Args:
            path: File path

        Returns:
            File contents

        Raises:
            PathNotFound: If file doesn't exist
        """
        ...

    async def delete_file(self, path: Path) -> None:
        """Delete file.

        Args:
            path: File to delete

        Raises:
            FileSystemError: If deletion fails
        """
        ...

    def file_exists(self, path: Path) -> bool:
        """Check if file exists.

        Args:
            path: File to check

        Returns:
            True if exists and is file
        """
        ...

    # Metadata
    async def get_modified_time(self, path: Path) -> float:
        """Get modification timestamp.

        Args:
            path: Path to check

        Returns:
            Modification time as unix timestamp

        Raises:
            PathNotFound: If path doesn't exist
        """
        ...

    async def get_size(self, path: Path) -> int:
        """Get file size.

        Args:
            path: File to check

        Returns:
            Size in bytes

        Raises:
            PathNotFound: If path doesn't exist
        """
        ...


# Legacy protocols for backward compatibility
ITerminalSession = TerminalSession
IArtifactExporter = ArtifactExporter
IMetadataStore = BuildRepository
IFileSystem = FileSystem
