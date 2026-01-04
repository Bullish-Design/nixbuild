# AGENTS.md

## Repository Overview

**nixbuild** is a minimal NixOS rebuild testing tool with terminal recording. It wraps `nixos-rebuild` commands with `asciinema` recording and structured JSON metadata output.

**Philosophy**: Simplicity over abstraction. This repo was refactored from ~3,300 lines to ~250 lines by removing unnecessary complexity. Maintain this minimalist approach.

## Architecture

```
CLI (Typer) → asyncio.subprocess → asciinema rec → nixos-rebuild
                                        ↓
                                 Structured Metadata (JSON)
```

### Key Files

| File | Purpose |
|------|---------|
| `src/nixos_rebuild_tester/nixbuild.py` | Core implementation (~250 lines) |
| `src/pyproject.toml` | Python package config |
| `flake.nix` | Nix flake with package, app, and devShell |

## Making Changes

### Adding CLI Commands

1. Add new command function with `@app.command()` decorator in `nixbuild.py`
2. Use Typer options/arguments for parameters
3. Keep async operations using `asyncio`

### Modifying Build Actions

The `RebuildAction` enum defines available actions:
- `test`, `build`, `dry-build`, `dry-activate`

To add new actions, extend the enum and handle in `run_nixos_rebuild()`.

### Output Format

Each build creates:
- `metadata.json` - Structured result data
- `rebuild.log` - Full text output  
- `session.cast` - Asciinema recording

Preserve this structure. The `metadata.json` schema is documented in README.md.

## Constraints

- **No complex abstractions**: No DI containers, domain models, or service layers
- **Direct subprocess**: Use `asyncio.create_subprocess_exec`, not pexpect/tmux
- **Native recording**: Use asciinema directly, not custom frame recording
- **Python 3.12+**: Target modern Python only
- **Single file core**: Keep main logic in one file unless significantly exceeds 500 lines

## Testing Changes

```bash
nix develop
uv pip install -e ./src
ruff check src/
ruff format src/

# Manual testing
nixos-rebuild-test run --action dry-build
nixos-rebuild-test list-builds
```

## Integration Points

This package is consumed by `nix-terminal` via:
- `nixbuild.packages.${system}.default` - The Python application
- Used in Home Manager module at `modules/nixbuild.nix`

Changes to CLI interface or output format may require updates to `nix-terminal`.

## Common Tasks

### Add a new CLI option
1. Add `typer.Option()` parameter to command function
2. Thread through to `run_nixos_rebuild()` if needed
3. Update README.md CLI Reference

### Modify metadata output
1. Update the `metadata` dict in `run_nixos_rebuild()`
2. Update README.md metadata schema documentation

### Add error handling
1. Add specific exception handling in the try/except block
2. Set appropriate exit code (124=timeout, 126=permission, 127=not found)
3. Populate `error_message` for metadata
