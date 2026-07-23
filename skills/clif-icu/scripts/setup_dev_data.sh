#!/usr/bin/env bash
#
# setup_dev_data.sh — stand up a NON-PHI CLIF dev sandbox for agent-assisted work.
#
# PHI-safe development means the AI agent only ever sees synthetic / demo data.
# This script bootstraps that sandbox in one command:
#   1. clone Common-Longitudinal-ICU-data-Format/synthetic_clif (MIT, no PHI) and
#      check out a PINNED ref (default v0.7.0) for reproducible provenance
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
#   Env: CLIF_SYNTHETIC_REF    synthetic_clif tag/branch/SHA to pin (default v0.7.0)
#        CLIF_DEV_TZ           timezone for the demo config       (default US/Central)
#        CLIF_SCHEMA_VERSION   target CLIF version 2.1|3.0        (default 2.1; the
#                              sandbox always emits 2.1 — 3.0 needs clifpy crosswalk)
#
# Failure-path tests (network-free): scripts/tests/test_setup_dev_data.sh
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
# Pin the synthetic_clif checkout to a specific ref so the CLI behavior and the
# synthetic-data provenance are reproducible — an unpinned branch can silently
# change between runs. Default: tag v0.7.0 (== main HEAD as of 2026-07-23; verify
# newer tags with `git ls-remote --tags $REPO_URL`). Override to track a different
# tag/branch/SHA, or set CLIF_SYNTHETIC_REF=main to intentionally follow upstream.
SYNTHETIC_REF="${CLIF_SYNTHETIC_REF:-v0.7.0}"
# CLIF schema version the caller intends to target. This sandbox always GENERATES
# CLIF 2.1 (that is what synthetic_clif emits), so 3.0 work must migrate the 2.1 data
# with clifpy's crosswalk as a deliberate, audited step — see the "CLIF version:
# 2.1 vs 3.0" section of the reference doc. We echo the caller's declared value so a
# wrong 2.1-vs-3.0 declaration is easy to spot up front (no automated detection).
CLIF_SCHEMA_VERSION="${CLIF_SCHEMA_VERSION:-2.1}"
case "$CLIF_SCHEMA_VERSION" in
  2.1|3.0) ;;
  *) echo "error: CLIF_SCHEMA_VERSION='$CLIF_SCHEMA_VERSION' unsupported (want 2.1 or 3.0)." >&2
     echo "See the \"CLIF version: 2.1 vs 3.0\" section of reference/phi-safe-development.md." >&2
     exit 2 ;;
esac

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
if [ "$CLIF_SCHEMA_VERSION" != "2.1" ]; then
  echo
  echo "NOTE: CLIF_SCHEMA_VERSION=$CLIF_SCHEMA_VERSION requested, but this sandbox emits"
  echo "CLIF 2.1. Migrate to $CLIF_SCHEMA_VERSION with clifpy's crosswalk (audited step) —"
  echo "see the \"CLIF version: 2.1 vs 3.0\" section of reference/phi-safe-development.md."
fi
echo

# 1. clone synthetic_clif and check out the pinned ref
if [ ! -d "$CLONE_DIR/.git" ]; then
  echo "Cloning $REPO_URL ..."
  git clone "$REPO_URL" "$CLONE_DIR"
fi
# Fetch (tags included) so the pinned ref resolves even in an existing checkout,
# then check it out. Fail fast if the ref does not exist rather than silently
# running whatever happens to be checked out.
echo "Pinning $CLONE_DIR to '$SYNTHETIC_REF' ..."
git -C "$CLONE_DIR" fetch --tags --quiet origin || echo "  (fetch failed; using local refs)"
if ! git -C "$CLONE_DIR" checkout --quiet "$SYNTHETIC_REF" 2>/dev/null; then
  echo "error: synthetic_clif ref '$SYNTHETIC_REF' not found." >&2
  echo "List available refs with:  git ls-remote --tags --heads $REPO_URL" >&2
  echo "Then re-run with:  CLIF_SYNTHETIC_REF=<tag-or-branch> $0 $*" >&2
  exit 2
fi
# Record the exact resolved commit so the provenance of the generated data is
# auditable (a tag or branch name alone can move; the SHA cannot).
RESOLVED_SHA="$(git -C "$CLONE_DIR" rev-parse --short HEAD)"
echo "  synthetic_clif @ $SYNTHETIC_REF ($RESOLVED_SHA)"

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
Generated from synthetic_clif $SYNTHETIC_REF ($RESOLVED_SHA).

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
