"""NixOS rebuild test automation with terminal recording."""

from __future__ import annotations

from nixos_rebuild_tester.application import Application
from nixos_rebuild_tester.domain.models import Config, RebuildAction, RebuildResult

__version__ = "0.1.0"
__all__ = ["Application", "Config", "RebuildAction", "RebuildResult"]
