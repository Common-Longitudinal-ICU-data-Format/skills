#!/usr/bin/env bash
#
# setup_dev_data.sh — stand up a NON-PHI CLIF dev sandbox for agent-assisted work.
#
# PHI-safe development means the AI agent only ever sees synthetic / demo data.
# This script bootstraps that sandbox in one command:
#   1. clone the source repo for the selected --source (synthetic_clif by default)
#      and check out a PINNED ref for reproducible provenance
#   2. synthetic-clif / clif-forge-generate: python3 -m pip install -e . and generate
#      a SMALL synthetic CLIF cohort into ./dev_data; clif-forge-sample: copy the
#      repo's committed sample_dataset/ parquet instead (no install, no generation)
#   3. write ./clif_demo_config.json pointing clifpy at ./dev_data
#
# The result is safe to share with an agent. See reference/phi-safe-development.md.
# It does NOT touch, download, or reference any real/PHI data.
#
# Usage:
#   scripts/setup_dev_data.sh [--source synthetic-clif|clif-forge-sample|clif-forge-generate]
#                              [--ref REF] [--config PATH] [DEST_DIR] [N_HOSPITALIZATIONS]
#     --source   where the sandbox data comes from (default: synthetic-clif)
#                  synthetic-clif       generate a fresh cohort with synthetic_clif
#                  clif-forge-sample    copy clif-forge's committed sample_dataset/
#                                       parquet as-is (no pip install, no generation)
#                  clif-forge-generate  generate a cohort with the clif-forge CLI
#     --ref      override the pinned ref (tag/branch/SHA) for the selected source's repo
#     --config   path to write the demo config to        (default: ./clif_demo_config.json)
#     DEST_DIR            where to write data             (default: ./dev_data)
#     N_HOSPITALIZATIONS  cohort size for fast iteration   (default: 100; unused by
#                                                            clif-forge-sample, which
#                                                            just copies what's committed)
#   Env: CLIF_SYNTHETIC_REF    synthetic_clif tag/branch/SHA to pin (default v0.7.0;
#                              --source synthetic-clif)
#        CLIF_FORGE_REF        clif-forge tag/branch/SHA to pin (default: verified main
#                              SHA — clif-forge has no tags yet, see below; --source
#                              clif-forge-sample | clif-forge-generate)
#        CLIF_DEV_TZ           timezone for the demo config       (default US/Central)
#        CLIF_SCHEMA_VERSION   target CLIF version 2.1|3.0        (default 2.1; the
#                              sandbox always emits 2.1 — 3.0 needs clifpy crosswalk)
#
# Failure-path tests (network-free): scripts/tests/test_setup_dev_data.sh
#
# Exit status: 0 = sandbox ready (data present + config written),
#              2 = setup/tooling error OR generation did not complete (empty sandbox).

set -euo pipefail

# --- flag parsing ------------------------------------------------------------
SOURCE="synthetic-clif"; REF_OVERRIDE=""; CONFIG_OVERRIDE=""; POS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --source) SOURCE="$2"; shift 2 ;;
    --ref)    REF_OVERRIDE="$2"; shift 2 ;;
    --config) CONFIG_OVERRIDE="$2"; shift 2 ;;
    -*) echo "error: unknown flag '$1' (see header comment for usage)" >&2; exit 2 ;;
    *) POS+=("$1"); shift ;;
  esac
done
set -- "${POS[@]+"${POS[@]}"}"
case "$SOURCE" in
  synthetic-clif|clif-forge-sample|clif-forge-generate) ;;
  *) echo "error: unknown --source '$SOURCE' (want synthetic-clif | clif-forge-sample | clif-forge-generate)" >&2; exit 2 ;;
esac

DEST_DIR="${1:-./dev_data}"
N_HOSP="${2:-100}"
CONFIG_PATH="${CONFIG_OVERRIDE:-./clif_demo_config.json}"
TIMEZONE="${CLIF_DEV_TZ:-US/Central}"

# Pin the checkout to a specific ref so the CLI behavior and the data provenance
# are reproducible — an unpinned branch can silently change between runs.
# synthetic-clif default: tag v0.7.0 (== main HEAD as of 2026-07-23; verify newer
# tags with `git ls-remote --tags <repo>`).
# clif-forge default: clif-forge has NO tags as of verification on 2026-07-31
# (`git ls-tree v0.2.0` fails; `git tag -l` is empty) — pinned instead to the
# verified main HEAD SHA below. Re-pin to a tag once clif-forge cuts one.
# Override either default with --ref, or CLIF_SYNTHETIC_REF=main /
# CLIF_FORGE_REF=main to intentionally follow upstream.
if [ "$SOURCE" = "synthetic-clif" ]; then
  REPO_URL="https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif"
  CLONE_DIR="./synthetic_clif"; PIN_REF="${REF_OVERRIDE:-${CLIF_SYNTHETIC_REF:-v0.7.0}}"
else
  REPO_URL="https://github.com/sajor2000/clif-forge"
  CLONE_DIR="./clif-forge"; PIN_REF="${REF_OVERRIDE:-${CLIF_FORGE_REF:-c29e0e0d101418aa898d0b7daa8250cecd178a3b}}"
fi

# CLIF schema version the caller intends to target. This sandbox always GENERATES
# CLIF 2.1 (that is what synthetic_clif and clif-forge emit), so 3.0 work must
# migrate the 2.1 data with clifpy's crosswalk as a deliberate, audited step —
# see the "CLIF version: 2.1 vs 3.0" section of the reference doc. We echo the
# caller's declared value so a wrong 2.1-vs-3.0 declaration is easy to spot up
# front (no automated detection).
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
# a declared dependency of any --source repo, so `pip install -e ...` does not pull
# it in. Preflight the EXACT symbol that step uses (not a bare `import clifpy`) so
# an older clifpy that imports but lacks create_example_config fails fast here,
# instead of aborting after the expensive clone/install/generate. This check runs
# before any clone for EVERY --source (fail-fast contract).
"$PY" -c 'from clifpy.utils.config import create_example_config' >/dev/null 2>&1 || {
  echo "error: clifpy (with clifpy.utils.config.create_example_config) is not importable with $PY." >&2
  echo "Install/upgrade it first, then re-run:  $PY -m pip install -U clifpy" >&2
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

# 1. clone the source repo and check out the pinned ref
if [ ! -d "$CLONE_DIR/.git" ]; then
  echo "Cloning $REPO_URL ..."
  git clone "$REPO_URL" "$CLONE_DIR"
fi
# Fetch (tags included) so the pinned ref resolves even in an existing checkout,
# then check it out. Fail fast if the ref does not exist rather than silently
# running whatever happens to be checked out.
echo "Pinning $CLONE_DIR to '$PIN_REF' ..."
git -C "$CLONE_DIR" fetch --tags --quiet origin || echo "  (fetch failed; using local refs)"
if ! git -C "$CLONE_DIR" checkout --quiet "$PIN_REF" 2>/dev/null; then
  echo "error: $SOURCE ref '$PIN_REF' not found." >&2
  echo "List available refs with:  git ls-remote --tags --heads $REPO_URL" >&2
  echo "Then re-run with --ref <tag-or-branch-or-SHA> (or the matching CLIF_*_REF env var)." >&2
  exit 2
fi
# Record the exact resolved commit so the provenance of the generated data is
# auditable (a tag or branch name alone can move; the SHA cannot).
RESOLVED_SHA="$(git -C "$CLONE_DIR" rev-parse --short HEAD)"
echo "  $SOURCE @ $PIN_REF ($RESOLVED_SHA)"

# 2. install + generate (or copy), per --source
generated=0
case "$SOURCE" in
  synthetic-clif)
    echo
    echo "Installing synthetic_clif (editable) ..."
    "$PY" -m pip install -e "$CLONE_DIR"
    mkdir -p "$DEST_DIR"
    echo
    echo "Generating ~$N_HOSP synthetic hospitalizations into $DEST_DIR ..."
    # Verified CLI (docs/tavily 2026-07-22): python -m synthetic_clif with
    # --hospitalizations/--output/--format/--seed. Run `"$PY" -m synthetic_clif
    # --help` as ground truth if flags have changed upstream.
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
    ;;
  clif-forge-sample)
    echo
    echo "Copying clif-forge's committed sample_dataset/ into $DEST_DIR (no generation) ..."
    if ls "$CLONE_DIR"/sample_dataset/clif_*.parquet >/dev/null 2>&1; then
      mkdir -p "$DEST_DIR"
      cp "$CLONE_DIR"/sample_dataset/clif_*.parquet "$DEST_DIR"/
      # keep manifest for provenance if present
      [ -f "$CLONE_DIR/sample_dataset/manifest.json" ] && cp "$CLONE_DIR/sample_dataset/manifest.json" "$DEST_DIR"/
      generated=1
    else
      echo "NOTE: no sample_dataset/clif_*.parquet found in $CLONE_DIR at $PIN_REF." >&2
    fi
    ;;
  clif-forge-generate)
    echo
    echo "Installing clif-forge (editable) ..."
    "$PY" -m pip install -e "$CLONE_DIR"
    mkdir -p "$DEST_DIR"
    echo
    echo "Generating ~$N_HOSP synthetic hospitalizations into $DEST_DIR ..."
    # CLI verified against clif-forge README (Quickstart), 2026-07-31: clif-forge
    # generate --preset <name> --n-patients N --out DIR. Ground-truth check if
    # flags have changed upstream: clif-forge --help
    if clif-forge generate --preset high-acuity --n-patients "$N_HOSP" --out "$DEST_DIR"; then
      generated=1
    else
      echo "NOTE: clif-forge generate failed; check flags with: clif-forge --help" >&2
    fi
    ;;
esac

# 3. write a demo config pointing at the non-PHI data (canonical clifpy JSON keys)
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

# Only declare success when data was actually generated/copied AND the destination
# is non-empty. Otherwise the "sandbox ready" banner + exit 0 would be a
# green-while-red signal: an agent (or the researcher) could conclude a non-PHI
# dataset exists when ./dev_data is empty, and be nudged to repoint the config at
# real PHI to "fix" it.
if [ "$generated" -eq 1 ] && [ -n "$(ls -A "$DEST_DIR" 2>/dev/null)" ]; then
  cat <<EOF

Done. Non-PHI sandbox ready.
Generated from $SOURCE @ $PIN_REF ($RESOLVED_SHA).

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
