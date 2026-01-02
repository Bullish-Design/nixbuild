# NixOS Rebuild Tester

Automated NixOS rebuild testing with terminal recording, visual artifacts, and structured metadata.

## Features

- 🎬 **Terminal Recording**: Capture complete rebuild sessions with timing information
- 📸 **Visual Artifacts**: Automatic screenshots and optional GIF animations
- 📊 **Structured Metadata**: Machine-readable JSON for CI/CD integration
- 🧹 **Smart Cleanup**: Configurable retention of build history
- 🔧 **Flexible CLI**: Easy-to-use command-line interface
- 🐍 **Programmatic API**: Use as a Python library

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
# Run a test rebuild (safe, doesn't activate)
nixos-rebuild-test run

# Run a dry-build (no sudo required)
nixos-rebuild-test run --action dry-build

# Export GIF animation
nixos-rebuild-test run --export-gif

# Keep only last 5 builds
nixos-rebuild-test run --keep-last 5

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

- `--action` - Rebuild action: `test`, `build`, `dry-build`, `dry-activate` (default: `test`)
- `--flake` - Flake reference (default: `.#`)
- `--output-dir` - Base output directory (default: `./rebuild-logs`)
- `--keep-last` - Keep only last N builds
- `--no-recording` - Disable terminal recording
- `--export-gif` - Export GIF animation (slow)
- `--timeout` - Maximum rebuild time in seconds (default: 1800)

**Examples:**

```bash
# Test rebuild of current flake
nixos-rebuild-test run

# Build a specific flake
nixos-rebuild-test run --action build --flake github:user/repo#hostname

# Quick dry-build without recording
nixos-rebuild-test run --action dry-build --no-recording

# Create shareable GIF
nixos-rebuild-test run --export-gif
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
    ├── rebuild.cast       # Asciinema recording
    ├── final.png          # Terminal screenshot
    └── rebuild.gif        # Animated GIF (optional)
```

### metadata.json Schema

```json
{
  "success": true,
  "exit_code": 0,
  "timestamp": "2026-01-02T14:30:22.123456",
  "duration_seconds": 127.3,
  "action": "test",
  "error_message": null,
  "files": {
    "log": "rebuild.log",
    "cast": "rebuild.cast",
    "screenshot": "final.png",
    "gif": null
  }
}
```

## Programmatic API

Use as a Python library:

```python
import asyncio
from nixos_rebuild_tester import Config, RebuildRunner, RebuildAction

# Configure
config = Config(
    rebuild=RebuildConfig(
        action=RebuildAction.DRY_BUILD,
        flake_ref=".#"
    ),
    output=OutputConfig(
        keep_last_n=5
    )
)

# Run
runner = RebuildRunner(config)
result = asyncio.run(runner.run())

# Check results
if result.success:
    print(f"Build succeeded in {result.duration_seconds:.1f}s")
else:
    print(f"Build failed: {result.error_message}")
```

## Use Cases

### Local Development

Test configuration changes before committing:

```bash
nixos-rebuild-test run --action dry-build
```

### CI/CD Integration

```yaml
- name: Test NixOS rebuild
  run: nix run .# -- run --no-recording --action build

- name: Upload logs on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    path: rebuild-logs/
```

### Documentation

Create visual guides:

```bash
nixos-rebuild-test run --export-gif
# Share rebuild.gif in wiki or PR
```

### Debugging

Analyze failures:

```bash
# Run multiple tests
for i in {1..10}; do nixos-rebuild-test run; done

# Find failures
nixos-rebuild-test list-builds | grep "✗"

# Review recordings
asciinema play rebuild-logs/rebuild-*/rebuild.cast
```

## Requirements

- NixOS or Nix with flakes enabled
- Python 3.12+
- tmux
- sudo access (for most rebuild actions)

## Architecture

Built on top of [terminal-state](https://github.com/Bullish-Design/terminal-state) for robust terminal recording:

```
CLI (Click) → Runner → TerminalSession (tmux) → nixos-rebuild
                    ↓
            Exporters (Asciinema, GIF, PNG)
                    ↓
            Structured Metadata (JSON)
```

## Documentation

- [CONCEPT.md](CONCEPT.md) - Project vision and design decisions
- [SPEC.md](SPEC.md) - Technical specification (coming soon)
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Implementation guide (coming soon)

## Development

```bash
# Enter development shell
nix develop

# Install in editable mode
uv pip install -e ./src

# Run tests
pytest tests/

# Run linter
ruff check src/

# Format code
ruff format src/
```

## License

MIT

## Contributing

Contributions welcome! Please see DEVELOPER_GUIDE.md for implementation details.

## Related Projects

- [terminal-state](https://github.com/Bullish-Design/terminal-state) - Terminal session recording library
- [asciinema](https://asciinema.org/) - Terminal session recorder (compatible format)
