"""Domain layer exports."""

from __future__ import annotations

from nixos_rebuild_tester.domain.models import (
    BuildArtifacts,
    Config,
    OutputConfig,
    RebuildAction,
    RebuildConfig,
    RebuildResult,
    RecordingConfig,
)
from nixos_rebuild_tester.domain.protocols import (
    IArtifactExporter,
    IFileSystem,
    IMetadataStore,
    ITerminalSession,
)
from nixos_rebuild_tester.domain.value_objects import Duration, TerminalDimensions, Timestamp

__all__ = [
    # Models
    "BuildArtifacts",
    "Config",
    "OutputConfig",
    "RebuildAction",
    "RebuildConfig",
    "RebuildResult",
    "RecordingConfig",
    # Protocols
    "IArtifactExporter",
    "IFileSystem",
    "IMetadataStore",
    "ITerminalSession",
    # Value Objects
    "Duration",
    "TerminalDimensions",
    "Timestamp",
]
