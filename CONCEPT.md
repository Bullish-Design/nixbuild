# NixOS Rebuild Tester - Concept Document

## Project Vision

Create an automated testing framework for NixOS system rebuilds that provides:
- Visual documentation via terminal recordings
- Structured output for analysis and debugging
- Programmatic API for integration
- CLI for manual testing

## Problem Statement

### Current Pain Points

**Manual rebuild testing is opaque:**
- No visual record of what happened
- Hard to debug failures after the fact
- Can't share build progress with teammates
- No structured data for trend analysis

**Existing solutions are inadequate:**
- Plain text logs lack timing information
- Can't replay the exact terminal state
- No automatic error detection
- Missing visual artifacts for documentation

### What This Solves

1. **Documentation**: Screenshots and recordings you can share in issues/PRs
2. **Debugging**: Frame-by-frame analysis of exactly what happened
3. **Automation**: Structured metadata for CI/CD integration
4. **History**: Keep last N builds with automatic cleanup

## Core Concepts

### 1. Terminal Recording

Instead of just capturing stdout/stderr, we capture the *actual terminal state* using tmux:

```
Normal logging:           Terminal recording:
└─ Text stream           └─ tmux session
   └─ rebuild.log           ├─ Frame 0 (t=0.0s)
                             ├─ Frame 1 (t=5.0s)
                             ├─ Frame 2 (t=10.0s)
                             └─ Frame N (t=127.3s)
```

Each frame captures:
- Exact terminal content at that moment
- Width/height of terminal
- Timestamp relative to start

### 2. Multi-Format Export

From a single recording, generate multiple artifacts:

```
Recording
├─→ .cast file (asciinema format, playable)
├─→ .log file (text dump of all frames)
├─→ .png file (screenshot of final state)
└─→ .gif file (animated progression, optional)
```

### 3. Structured Metadata

Every rebuild produces machine-readable JSON:

```json
{
  "success": false,
  "exit_code": 1,
  "timestamp": "2026-01-02T14:30:22.123456",
  "duration_seconds": 127.3,
  "action": "test",
  "error_message": "error: builder for '/nix/store/...-foo' failed",
  "files": {
    "log": "rebuild.log",
    "cast": "rebuild.cast",
    "screenshot": "final.png",
    "gif": "rebuild.gif"
  }
}
```

This enables:
- Automated analysis (CI/CD pass/fail detection)
- Trend tracking (average build times)
- Dashboard creation
- API integration

### 4. Smart Cleanup

Prevent disk bloat with configurable retention:

```
rebuild-logs/
├── rebuild-20260102-143022/  ← Keep (newest)
├── rebuild-20260102-120045/  ← Keep
├── rebuild-20260101-093011/  ← Keep
├── rebuild-20260101-081544/  ← Keep
└── rebuild-20250731-152033/  ← Delete (> keep_last_n)
```

## Architecture Overview

### High-Level Flow

```
User runs CLI
    ↓
Config loaded (from args/defaults)
    ↓
Output directory created (timestamped)
    ↓
Terminal session started (tmux backend)
    ↓
Rebuild command sent to session
    ↓
Periodic frame capture (every 5s)
    ↓
Error detection in real-time
    ↓
Session closed
    ↓
Artifacts exported (.cast, .log, .png, .gif)
    ↓
Metadata saved (.json)
    ↓
Old builds cleaned up
    ↓
Result returned to user
```

### Component Layers

```
┌─────────────────────────────────────┐
│     CLI (Click interface)           │
│  - run command                      │
│  - list-builds command              │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│     Runner (orchestration)          │
│  - Create output directories        │
│  - Execute rebuilds                 │
│  - Manage recordings                │
│  - Export artifacts                 │
│  - Clean up old builds              │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  terminal-state (external library)  │
│  - TerminalSession                  │
│  - Recording                        │
│  - Exporters (Asciinema, GIF, PNG)  │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│     tmux (system dependency)        │
│  - Provides pseudo-terminal         │
│  - Manages session lifecycle        │
└─────────────────────────────────────┘
```

## Key Design Decisions

### Why tmux Instead of Direct PTY?

**Pros:**
- terminal-state already provides tmux backend
- tmux handles all PTY complexity
- Sessions can be inspected manually if needed

**Cons:**
- ~500ms startup overhead
- Requires tmux installation
- Extra memory usage (~50-100MB)

**Decision:** Use tmux. The benefits outweigh the overhead for this use case.

### Why Pydantic for Models?

**Pros:**
- Runtime validation prevents bad configs
- Type safety catches bugs early
- Serialization to/from JSON is trivial
- Self-documenting via Field descriptions

**Cons:**
- Slight performance overhead
- Extra dependency

**Decision:** Use Pydantic. Type safety is critical for junior developers.

### Why Both .cast and .log Files?

**.cast (asciinema format):**
- Preserves timing
- Playable with `asciinema play`
- Industry standard format

**.log (plain text):**
- Easy to grep/search
- Works in environments without asciinema
- Better for CI log aggregation

**Decision:** Generate both. Disk is cheap, flexibility is valuable.

### Why Optional GIF Export?

**Pros:**
- Shareable in GitHub issues/PRs
- No tooling required to view
- Great for documentation

**Cons:**
- Very slow (can add 30-60s per build)
- Large file sizes (5-10MB)
- Overkill for routine testing

**Decision:** Make it optional (disabled by default).

## Use Cases

### UC1: Local Development Testing

Developer makes config changes and wants to test before committing:

```bash
nixos-rebuild-test run
# See visual feedback
# Share screenshot if build fails
```

### UC2: CI/CD Pipeline

GitHub Actions runs automated testing:

```yaml
- name: Test rebuild
  run: nix run .# -- run --no-recording --action build

- name: Upload logs on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    path: rebuild-logs/
```

### UC3: Documentation Creation

Creating rebuild guide for team:

```bash
nixos-rebuild-test run --export-gif
# Embed rebuild.gif in wiki
# Show exact steps visually
```

### UC4: Historical Analysis

Tracking build performance over time:

```bash
# Keep last 30 builds
nixos-rebuild-test run --keep-last 30

# Later, parse all metadata.json files
jq '.duration_seconds' rebuild-logs/*/metadata.json
```

### UC5: Debugging Nondeterministic Failures

Build fails occasionally but not consistently:

```bash
# Run multiple times
for i in {1..10}; do
  nixos-rebuild-test run
done

# Review only failures
nixos-rebuild-test list-builds | grep "✗"
```

## Non-Goals

**What this project does NOT do:**

1. **Replace nixos-rebuild**: We wrap it, not replace it
2. **Auto-fix failures**: We document failures, not fix them
3. **Optimize build times**: We measure them, not improve them
4. **Manage NixOS configs**: We test whatever config exists
5. **Provide shell integration**: Unlike term-record, we don't hook shells

## Success Criteria

**MVP is successful if:**

1. Can run `nixos-rebuild test` in a recorded session
2. Captures terminal output as .cast file
3. Exports final screenshot as .png
4. Saves metadata.json with success/failure
5. CLI works: `nixos-rebuild-test run`
6. Works on NixOS with flakes enabled

**Full release is successful if:**

1. All MVP criteria met
2. Optional GIF export works
3. `list-builds` command shows history
4. `--keep-last N` cleanup works
5. Error messages are extracted and shown
6. Documentation is complete
7. Tests pass

## Future Enhancements

**Post-MVP features:**

1. **Diff visualization**: Compare two builds side-by-side
2. **Phase detection**: Automatically detect "evaluating", "building", "activating"
3. **Web dashboard**: Browse build history in browser
4. **Notifications**: Send Discord/Slack message on failure
5. **Parallel testing**: Test multiple configs simultaneously
6. **Performance metrics**: CPU/memory usage during build
7. **Integration with term-record**: Link to shell history via atuin

## Risk Assessment

### Technical Risks

**Risk 1: tmux not available**
- Likelihood: Low (we're on NixOS, can package it)
- Impact: High (breaks entire system)
- Mitigation: Require tmux in flake dependencies

**Risk 2: Builds timeout**
- Likelihood: Medium (large configs can take 30+ min)
- Impact: Medium (wasted time)
- Mitigation: Configurable timeout with sensible default (30 min)

**Risk 3: Disk fills up**
- Likelihood: Medium (GIFs are 5-10MB each)
- Impact: High (breaks CI)
- Mitigation: Cleanup with `--keep-last`, warn if disk low

**Risk 4: Error detection is unreliable**
- Likelihood: High (parsing terminal output is fragile)
- Impact: Low (worst case: misreport success/failure)
- Mitigation: Document limitations, consider exit code fallback

### Process Risks

**Risk 1: Junior developer gets stuck**
- Likelihood: Medium (complex async/tmux interaction)
- Impact: High (delays project)
- Mitigation: Provide detailed DEVELOPER_GUIDE.md with examples

**Risk 2: Scope creep**
- Likelihood: High (many "nice to have" features)
- Impact: Medium (delays MVP)
- Mitigation: Strict MVP definition, defer enhancements

## Open Questions

1. **Should we support non-flake nixos-rebuild?**
   - Probably yes, just change the `--flake` arg handling

2. **Should recording be synchronous or async?**
   - Async for frame capture, but rebuild itself is blocking

3. **How do we handle interactive prompts?**
   - nixos-rebuild might ask for confirmation
   - Solution: Always run with `--no-build-output` or similar

4. **Should we support other actions besides test/build?**
   - Yes: dry-build, dry-activate, boot, switch
   - But warn that switch/boot require sudo and affect system

5. **Should metadata.json include derivation info?**
   - Nice to have: which packages changed
   - Requires parsing nix output
   - Defer to post-MVP

## Summary

This project bridges the gap between "quick test" and "thorough documentation" by making NixOS rebuilds:
- Observable (visual artifacts)
- Analyzable (structured data)
- Shareable (standard formats)
- Automated (CLI + API)

The terminal-state library handles the complex parts (tmux, recording, export), letting us focus on the workflow (run, capture, save, cleanup).
