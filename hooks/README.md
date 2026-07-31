# Claude Code Hooks for clif-icu

## Overview

This directory contains PreToolUse hooks that enforce PHI-safe workflows in Claude Code sessions for clif-icu work.

### phi_guard.py (PHI blocker)

Blocks agent tool access to real-data directories configured by your site. Enforces the PHI-safe development workflow documented in `skills/clif-icu/reference/phi-safe-development.md`.

**How it works:** The hook reads a configuration file listing directories containing real (PHI) data. When an agent attempts to use tools like `Read`, `Glob`, or `Bash`, the hook checks whether the command or path references a configured PHI directory. If so, the command is blocked with an explanatory message.

**Contract:** Exit 0 = allow; exit 2 + stderr message = block.

### phi_scan.py (output scanner, advisory)

Scans command output for suspected PHI patterns and warns the agent (advisory, non-blocking). When PHI-shaped data is detected, the agent is instructed to stop and sanitize its response. Synthetic data will trigger false positives by design — the warning message explains how to proceed if the data is confirmed non-PHI.

**How it works:** The hook examines the tool's response text for patterns that resemble medical record numbers, social security numbers, and birth dates. If any patterns are found, it prints a JSON warning to stdout and exits with code 0 (advisory, never blocks). Set `CLIF_PHI_SCAN=off` to disable scanning.

## Configuration

### PHI Paths Config File

The guard reads from the union of all existing files in this list:
1. `$CLIF_PHI_PATHS_FILE` environment variable (if set to a valid path)
2. `./.clif-phi-paths` in the current working directory
3. `~/.clif/phi-paths` in your home directory

**Format:** One directory path per line. Lines starting with `#` are comments. Empty lines are ignored.

**Example:**
```
# Real patient data at this site
/data/umich/real_data
/scratch/cohort_exports
# Archive from last year
/archive/2024/raw
```

### Activation

The guard is **inactive until a config file exists**. If none of the three config sources are present, the hook allows all operations. This lets you opt in to PHI protection.

## Known Limitations

This is **risk-reduction defense-in-depth, not a sandbox and not compliance**. Be aware of:

- **Bash matching is substring-only:** Relative paths (e.g., `cd subdir && head file.csv`), paths assembled via shell variables (e.g., `$data_path/file.csv`), or shell globbing are not caught by the guard. Always use absolute paths to PHI data in your scripts, and keep them out of Claude Code.

- **Case-sensitive filesystems:** On case-insensitive filesystems (e.g., macOS APFS), the guard compares both exact and casefolded paths to catch case variants. On case-sensitive filesystems, this may over-block legitimate reads to paths that differ only in casing from configured PHI directories (acceptable for a guardrail).

- **Claude Code only:** This hook only works within Claude Code sessions. Other tools (direct Python, shell, data pipeline orchestrators) receive no mechanical guard. You are responsible for keeping PHI data out of those contexts.

- **Guardian, not barrier:** The guard is risk mitigation. Determined agent misuse (modifying config, forking processes, using eval patterns) may circumvent it. Use social controls, file permissions, and code review alongside this tool.

- **Inactive until configured:** The guard has no effect if none of the three config sources exist (env var, `.clif-phi-paths`, `~/.clif/phi-paths`). This is by design — you opt in to PHI protection by creating a config file.

For more on PHI-safe development practices, see `skills/clif-icu/reference/phi-safe-development.md`.
