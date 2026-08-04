#!/usr/bin/env python3
"""clif-icu PHI guard (PreToolUse).

Blocks agent tool access to real-data directories the site lists in a config
file. Mechanical enforcement of the PHI-safe workflow in
skills/clif-icu/reference/phi-safe-development.md.

Config: newline-delimited directory paths ('#' comments allowed) from ALL of:
  $CLIF_PHI_PATHS_FILE, ./.clif-phi-paths, ~/.clif/phi-paths  (union of those
  that exist). No config => allow everything (guard inactive until configured).

Contract: exit 0 allow; exit 2 block (stderr shown to the agent). Stdlib only.
"""
import json, os, sys

PATH_KEYS = ("file_path", "path", "notebook_path")
TEXT_KEYS = ("command",)  # Bash


def config_sources():
    return [os.environ.get("CLIF_PHI_PATHS_FILE"),
            os.path.join(os.getcwd(), ".clif-phi-paths"),
            os.path.expanduser("~/.clif/phi-paths")]


def load_phi_paths():
    """Return [(raw_line, realpath)] for every configured PHI dir."""
    out = []
    for src in config_sources():
        if not src or not os.path.isfile(src):
            continue
        try:
            with open(src) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        out.append((line, os.path.realpath(os.path.expanduser(line))))
        except OSError:
            continue
    return out


def is_under(target, root):
    t = os.path.realpath(os.path.expanduser(target))
    if t == root or t.startswith(root + os.sep):
        return True
    tf, rf = t.casefold(), root.casefold()
    return tf == rf or tf.startswith(rf + os.sep)


def block(value, raw):
    sys.stderr.write(
        f"BLOCKED by clif-icu PHI guard: '{value}' is inside the configured "
        f"real-data path '{raw}'. Agents must never receive PHI. Use the "
        "non-PHI sandbox (skills/clif-icu/scripts/setup_dev_data.sh); see "
        "reference/phi-safe-development.md. To change guarded paths, edit "
        "the PHI paths config (.clif-phi-paths / ~/.clif/phi-paths).\n")
    return 2


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # malformed input: never break the session
    if not isinstance(data, dict):
        return 0
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0
    phi = load_phi_paths()
    if not phi:
        return 0
    for key in PATH_KEYS:
        v = tool_input.get(key)
        if isinstance(v, str):
            for raw, root in phi:
                if is_under(v, root):
                    return block(v, raw)
    for key in TEXT_KEYS:
        v = tool_input.get(key)
        if isinstance(v, str):
            for raw, root in phi:
                # conservative substring check on command text, raw + resolved
                if raw in v or root in v:
                    return block(key + ": " + v[:120], raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
