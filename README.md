# NixOS Rebuild Tester

Minimal NixOS rebuild testing with terminal recording - refactored from complex over-engineered architecture to simple direct subprocess approach.

## Features

- 🎬 **Terminal Recording**: Capture complete rebuild sessions with asciinema
- 📊 **Structured Metadata**: Machine-readable JSON for CI/CD integration
- 🔧 **Simple CLI**: Minimal command-line interface built with Typer
- 🚀 **Direct Subprocess**: No complex abstractions - just asyncio + subprocess

## Quick Start

### Installation

```bash
# Run directly with Nix
nix run github:Bullish-Design/nixbuild

# Or clone and develop locally
git clone https://github.com/Bullish-Design/nixbuild
cd nixbuild
nix develop
uv pip install -e ./src
```

### Basic Usage

```bash
# Run a dry-build (safe, doesn't activate)
nixos-rebuild-test run

# Run a test rebuild
nixos-rebuild-test run --action test

# Specify custom flake
nixos-rebuild-test run --flake github:user/repo#hostname

# List recent builds
nixos-rebuild-test list-builds
```

## CLI Reference

### `run` Command

Execute a NixOS rebuild with recording:

```bash
nixos-rebuild-test run [OPTIONS]
```

**Options:**

- `--action` - Rebuild action: `test`, `build`, `dry-build`, `dry-activate` (default: `dry-build`)
- `--flake` - Flake reference (default: `.#`)
- `--output-dir` - Base output directory (default: `./rebuild-logs`)
- `--timeout` - Maximum rebuild time in seconds (default: 1800)

**Examples:**

```bash
# Dry-build of current flake (default)
nixos-rebuild-test run

# Test rebuild
nixos-rebuild-test run --action test

# Build a specific flake
nixos-rebuild-test run --action build --flake github:user/repo#hostname

# Quick dry-build with short timeout
nixos-rebuild-test run --timeout 300
```

### `list-builds` Command

List recent rebuild attempts:

```bash
nixos-rebuild-test list-builds [OPTIONS]
```

**Options:**

- `--output-dir` - Directory to list (default: `./rebuild-logs`)
- `--limit` - Number of builds to show (default: 10)

## Output Format

Each rebuild creates a timestamped directory:

```
rebuild-logs/
└── rebuild-20260102-143022/
    ├── metadata.json      # Structured result data
    ├── rebuild.log        # Full text output
    └── session.cast       # Asciinema recording
```

### metadata.json Schema

```json
{
  "success": true,
  "exit_code": 0,
  "action": "dry-build",
  "flake_ref": ".#",
  "timestamp": "2026-01-02T14:30:22.123456",
  "duration_seconds": 127.3,
  "error_message": null,
  "artifacts": {
    "log": "rebuild.log",
    "cast": "session.cast"
  }
}
```

## Use Cases

### Local Development

Test configuration changes before committing:

```bash
nixos-rebuild-test run
```

### CI/CD Integration

```yaml
- name: Test NixOS rebuild
  run: nix run .# -- run --action build

- name: Upload logs on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    path: rebuild-logs/
```

### Debugging

Analyze failures:

```bash
# Run test
nixos-rebuild-test run --action test

# List recent builds
nixos-rebuild-test list-builds

# Review recording
asciinema play rebuild-logs/rebuild-*/session.cast
```

## Requirements

- NixOS or Nix with flakes enabled
- Python 3.12+
- asciinema (for terminal recording)
- sudo access (for most rebuild actions)

## Architecture

Simple direct approach:

```
CLI (Typer) → asyncio.subprocess → asciinema rec → nixos-rebuild
                                           ↓
                                    Structured Metadata (JSON)
```

**Key simplifications:**
- Direct subprocess calls instead of tmux + pexpect
- Native asciinema recording instead of custom frame recording
- Simple error extraction instead of complex error detection service
- No DI container, domain models, or abstraction layers

See [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) for full refactoring details.

## Documentation

- [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Refactoring from complex to minimal architecture
- [CONCEPT.md](CONCEPT.md) - Original project vision

## Development

```bash
# Enter development shell
nix develop

# Install in editable mode
uv pip install -e ./src

# Run linter
ruff check src/

# Format code
ruff format src/
```

## What Changed in v0.2.0

**Removed:**
- Complex domain models (RebuildSession, ExecutionOutcome, etc.)
- Service layer (BuildExecutor, CommandRunner, FrameRecorder, etc.)
- Adapter layer (TerminalStateSessionAdapter, exporters)
- DI container and application facade
- terminal-state dependency
- tmux + pexpect integration
- GIF/screenshot export
- Complex error detection

**Added:**
- Single minimal implementation (~250 lines)
- Direct subprocess execution
- Native asciinema recording
- Simple error extraction

**Result:**
- 94% reduction in code (3,300 → 250 lines)
- 95% reduction in files (38 → 2 files)
- 80% reduction in dependencies
- Same core functionality

## License

MIT

## Related Projects

- [asciinema](https://asciinema.org/) - Terminal session recorder
