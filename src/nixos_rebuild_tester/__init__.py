"""Minimal NixOS rebuild testing with terminal recording.

Refactored from complex over-engineered architecture to simple direct subprocess approach.
See REFACTORING_GUIDE.md for details on the refactoring.
"""

from nixos_rebuild_tester.nixbuild import main

__all__ = ["main"]
__version__ = "0.2.0"
