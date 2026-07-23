#!/usr/bin/env bash
#
# setup_dev_data.sh — stand up a NON-PHI CLIF dev sandbox for agent-assisted work.
#
# PHI-safe development means the AI agent only ever sees synthetic / demo data.
# This script bootstraps that sandbox in one command:
#   1. clone (or update) Common-Longitudinal-ICU-data-Format/synthetic_clif (MIT, no PHI)
#   2. python3 -m pip install -e .
#   3. generate a SMALL synthetic CLIF cohort into ./dev_data
#   4. write ./clif_demo_config.json pointing clifpy at ./dev_data
#
# The result is safe to share with an agent. See reference/phi-safe-development.md.
# It does NOT touch, download, or reference any real/PHI data.
#
# Usage:
#   scripts/setup_dev_data.sh [DEST_DIR] [N_HOSPITALIZATIONS]
#     DEST_DIR            where to write generated data (default: ./dev_data)
#     N_HOSPITALIZATIONS  cohort size for fast iteration  (default: 100)
#
# Exit status: 0 = sandbox ready (data generated + config written),
#              2 = setup/tooling error OR generation did not complete (empty sandbox).

set -euo pipefail

DEST_DIR="${1:-./dev_data}"
N_HOSP="${2:-100}"
REPO_URL="https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif"
CLONE_DIR="./synthetic_clif"
CONFIG_PATH="./clif_demo_config.json"
TIMEZONE="${CLIF_DEV_TZ:-US/Central}"

command -v git >/dev/null 2>&1 || { echo "error: git not found" >&2; exit 2; }
# Prefer python3, fall back to python. Route ALL python/pip calls through "$PY"
# so the script does not abort under `set -euo pipefail` on a missing `python`.
if command -v python3 >/dev/null 2>&1; then
  PY="python3"
elif command -v python >/dev/null 2>&1; then
  PY="python"
else
  echo "error: neither python3 nor python found" >&2; exit 2
fi

# clifpy is required for the config-writing step (create_example_config) but is NOT
# a declared dependency of synthetic_clif, so `pip install -e synthetic_clif` does
# not pull it in. Preflight here so we fail fast with a clear instruction instead of
# aborting with a ModuleNotFoundError after the expensive clone/install/generate.
"$PY" -c 'import clifpy' >/dev/null 2>&1 || {
  echo "error: clifpy is not importable with $PY." >&2
  echo "Install it first, then re-run:  $PY -m pip install clifpy" >&2
  exit 2
}

echo "== PHI-safe dev-data setup =="
echo "This creates NON-PHI synthetic CLIF data only. Never point clifpy at real"
echo "PHI while an agent can see the output (see reference/phi-safe-development.md)."
echo

# 1. clone or update synthetic_clif
if [ -d "$CLONE_DIR/.git" ]; then
  echo "Updating existing $CLONE_DIR ..."
  git -C "$CLONE_DIR" pull --ff-only || echo "  (could not fast-forward; using existing checkout)"
else
  echo "Cloning $REPO_URL ..."
  git clone "$REPO_URL" "$CLONE_DIR"
fi

# 2. install
echo "Installing synthetic_clif (editable) ..."
"$PY" -m pip install -e "$CLONE_DIR"

# 3. generate a small cohort with the verified synthetic_clif CLI
mkdir -p "$DEST_DIR"
echo
echo "Generating ~$N_HOSP synthetic hospitalizations into $DEST_DIR ..."
# Verified CLI (docs/tavily 2026-07-22): python -m synthetic_clif with
# --hospitalizations/--output/--format/--seed. Run `"$PY" -m synthetic_clif --help`
# as ground truth if flags have changed upstream.
generated=0
if "$PY" -m synthetic_clif --hospitalizations "$N_HOSP" --output "$DEST_DIR" \
        --format parquet --seed 42; then
  generated=1
fi

if [ "$generated" -eq 0 ]; then
  echo
  echo "NOTE: synthetic_clif generation did not complete with the expected CLI."
  echo "Check the current flags with:"
  echo "    $PY -m synthetic_clif --help"
  echo "or generate manually (see $CLONE_DIR/README), or download a pre-generated"
  echo "release from: $REPO_URL"
  echo "The config below will point clifpy at $DEST_DIR once data is present."
fi

# 4. write a demo config pointing at the non-PHI data (canonical clifpy JSON keys)
echo
echo "Writing $CONFIG_PATH ..."
"$PY" - "$DEST_DIR" "$TIMEZONE" "$CONFIG_PATH" <<'PY'
import sys
from clifpy.utils.config import create_example_config

data_directory, timezone, config_path = sys.argv[1:4]
create_example_config(
    data_directory=data_directory,
    filetype="parquet",
    timezone=timezone,
    output_directory="./output",
    config_path=config_path,
)
print(f"  wrote {config_path} -> data_directory={data_directory}")
PY

# Only declare success when data was actually generated AND the destination is
# non-empty. Otherwise the "sandbox ready" banner + exit 0 would be a green-while-red
# signal: an agent (or the researcher) could conclude a non-PHI dataset exists when
# ./dev_data is empty, and be nudged to repoint the config at real PHI to "fix" it.
if [ "$generated" -eq 1 ] && [ -n "$(ls -A "$DEST_DIR" 2>/dev/null)" ]; then
  cat <<EOF

Done. Non-PHI sandbox ready.

Load it with:
    from clifpy import ClifOrchestrator
    co = ClifOrchestrator(config_path="$CONFIG_PATH")

This data is synthetic and safe to share with an agent. Real PHI must only be run
by you, in your own secure environment, with the agent absent.
EOF
else
  cat >&2 <<EOF

Sandbox NOT ready: no synthetic data was generated in $DEST_DIR.
$CONFIG_PATH was written but points at an empty directory. Do NOT repoint it at
real PHI to "get things working" — that is exactly the unsafe fallback this setup
exists to prevent. Generate the synthetic data first (see the NOTE above), then
re-run this script.
EOF
  exit 2
fi
