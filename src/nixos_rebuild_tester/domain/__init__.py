"""Domain layer exports."""

from __future__ import annotations

from nixos_rebuild_tester.domain.exceptions import (
    BuildFailed,
    BuildNotFound,
    CorruptedMetadata,
    DirectoryCreationFailed,
    ExportError,
    ExportFailed,
    ExporterNotFound,
    ExecutionError,
    ExecutionTimeout,
    FileSystemError,
    InsufficientPermissions,
    InvalidFlakeRef,
    PathNotFound,
    PathNotWritable,
    RebuildTesterError,
    SessionCrashed,
    SessionCreationFailed,
    SessionError,
    SessionTimeout,
    StorageError,
)
from nixos_rebuild_tester.domain.models import (
    BuildArtifacts,
    Config,
    ExecutionOutcome,
    OutputConfig,
    RebuildAction,
    RebuildConfig,
    RebuildResult,
    RebuildSession,
    RecordingConfig,
    SessionState,
    TestResult,
)
from nixos_rebuild_tester.domain.neovim_models import (
    KeyModifier,
    KeyStroke,
    NeovimCommand,
    NeovimTestConfig,
)
from nixos_rebuild_tester.domain.protocols import (
    ArtifactExporter,
    BuildRepository,
    FileSystem,
    TerminalSession,
)
from nixos_rebuild_tester.domain.value_objects import (
    BuildId,
    Duration,
    ErrorMessage,
    ErrorSource,
    OutputDirectory,
    TerminalDimensions,
    Timestamp,
)

__all__ = [
    # Models
    "BuildArtifacts",
    "Config",
    "ExecutionOutcome",
    "OutputConfig",
    "RebuildAction",
    "RebuildConfig",
    "RebuildResult",
    "RebuildSession",
    "RecordingConfig",
    "SessionState",
    "TestResult",
    # Neovim Models
    "KeyModifier",
    "KeyStroke",
    "NeovimCommand",
    "NeovimTestConfig",
    # Protocols
    "ArtifactExporter",
    "BuildRepository",
    "FileSystem",
    "TerminalSession",
    # Value Objects
    "BuildId",
    "Duration",
    "ErrorMessage",
    "ErrorSource",
    "OutputDirectory",
    "TerminalDimensions",
    "Timestamp",
    # Exceptions
    "BuildFailed",
    "BuildNotFound",
    "CorruptedMetadata",
    "DirectoryCreationFailed",
    "ExportError",
    "ExportFailed",
    "ExporterNotFound",
    "ExecutionError",
    "ExecutionTimeout",
    "FileSystemError",
    "InsufficientPermissions",
    "InvalidFlakeRef",
    "PathNotFound",
    "PathNotWritable",
    "RebuildTesterError",
    "SessionCrashed",
    "SessionCreationFailed",
    "SessionError",
    "SessionTimeout",
    "StorageError",
]
