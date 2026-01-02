"""Persistence adapters for storing build results."""

from __future__ import annotations

from nixos_rebuild_tester.adapters.persistence.filesystem_repository import FileSystemBuildRepository

__all__ = ["FileSystemBuildRepository"]
