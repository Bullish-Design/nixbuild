"""Domain-specific exception hierarchy."""

from __future__ import annotations


class RebuildTesterError(Exception):
    """Base exception for all domain errors."""


class SessionError(RebuildTesterError):
    """Terminal session errors."""


class SessionCreationFailed(SessionError):
    """Failed to create terminal session."""


class SessionTimeout(SessionError):
    """Session operation timed out."""


class SessionCrashed(SessionError):
    """Session unexpectedly terminated."""


class ExecutionError(RebuildTesterError):
    """Rebuild execution errors."""


class BuildFailed(ExecutionError):
    """Rebuild itself failed (expected failure)."""


class ExecutionTimeout(ExecutionError):
    """Execution exceeded timeout."""


class InvalidFlakeRef(ExecutionError):
    """Invalid flake reference provided."""


class ExportError(RebuildTesterError):
    """Artifact export errors."""


class ExporterNotFound(ExportError):
    """Requested exporter not available."""


class ExportFailed(ExportError):
    """Export operation failed."""


class StorageError(RebuildTesterError):
    """Persistence errors."""


class BuildNotFound(StorageError):
    """Build result not found in storage."""


class CorruptedMetadata(StorageError):
    """Metadata file is corrupted or invalid."""


class DirectoryCreationFailed(StorageError):
    """Failed to create output directory."""


class FileSystemError(RebuildTesterError):
    """Filesystem operation errors."""


class PathNotFound(FileSystemError):
    """Required path does not exist."""


class PathNotWritable(FileSystemError):
    """Path is not writable."""


class InsufficientPermissions(FileSystemError):
    """Insufficient permissions for operation."""
