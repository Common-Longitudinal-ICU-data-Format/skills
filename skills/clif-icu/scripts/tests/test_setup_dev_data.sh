#!/usr/bin/env bash
#
# test_setup_dev_data.sh — failure-path tests for scripts/setup_dev_data.sh.
#
# These are NETWORK-FREE: git and the python interpreter are replaced with stubs
# on PATH, so the real clone/install/generate never runs. The point is to lock in
# the safety contract that a live run cannot easily exercise:
#   - clifpy preflight fails FAST, before any clone (finding: fresh-sandbox failure)
#   - a failed or empty generation NEVER prints "sandbox ready" and exits non-zero
#     (finding: green-while-red)
#   - a bad pin ref fails loudly instead of silently running whatever is checked out
#
# Usage:  scripts/tests/test_setup_dev_data.sh
# Exit status: 0 = all cases passed, 1 = a case failed.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../setup_dev_data.sh"

[ -f "$SCRIPT" ] || { echo "FAIL: cannot find $SCRIPT" >&2; exit 1; }

fails=0

# ---------------------------------------------------------------------------
# Build a stub PATH. git and python3 are fakes whose behavior is toggled by
# STUB_* env vars set per case. Real coreutils (mkdir, ls, cat, ...) stay live
# because the stub bin dir is only PREPENDED to PATH.
# ---------------------------------------------------------------------------
STUBDIR="$(mktemp -d)"
trap 'rm -rf "$STUBDIR"' EXIT

cat > "$STUBDIR/git" <<'STUB'
#!/usr/bin/env bash
# Minimal git stub for setup_dev_data.sh.
case "$1" in
  clone)                                       # git clone URL DIR
    mkdir -p "$3/.git"
    if [ "${STUB_GIT_MAKE_SAMPLE:-0}" = "1" ]; then
      mkdir -p "$3/sample_dataset"
      echo x > "$3/sample_dataset/clif_vitals.parquet"
    fi
    exit 0 ;;
  -C)
    sub="$3"
    case "$sub" in
      fetch)     exit 0 ;;
      checkout)  ref="${@: -1}"                # git -C DIR checkout --quiet REF
                 if [ -n "${STUB_BAD_REF:-}" ] && [ "$ref" = "$STUB_BAD_REF" ]; then
                   exit 1
                 fi
                 exit 0 ;;
      rev-parse) echo "deadbee"; exit 0 ;;
    esac ;;
esac
exit 0
STUB

cat > "$STUBDIR/python3" <<'STUB'
#!/usr/bin/env bash
# Minimal python interpreter stub for setup_dev_data.sh.
if [ "${1:-}" = "-c" ]; then                   # clifpy preflight import
  [ -n "${STUB_FAIL_CLIFPY:-}" ] && exit 1
  # Simulate an OLDER clifpy that imports but lacks create_example_config:
  # the preflight imports the exact symbol, so this branch must fail on it.
  if [ -n "${STUB_OLD_CLIFPY:-}" ] && [[ "${2:-}" == *create_example_config* ]]; then
    exit 1
  fi
  exit 0
fi
if [ "${1:-}" = "-m" ]; then
  case "${2:-}" in
    pip) exit 0 ;;                             # pip install -e .
    synthetic_clif)
      [ -n "${STUB_FAIL_GEN:-}" ] && exit 1
      # Honor --output DEST; optionally write a table so the dir is non-empty.
      dest=""; prev=""
      for a in "$@"; do
        [ "$prev" = "--output" ] && dest="$a"
        prev="$a"
      done
      if [ -n "${STUB_GEN_WRITES_FILES:-}" ] && [ -n "$dest" ]; then
        mkdir -p "$dest"; : > "$dest/clif_patient.parquet"
      fi
      exit 0 ;;
  esac
fi
if [ "${1:-}" = "-" ]; then                    # heredoc config writer
  cat >/dev/null                               # "-" data_dir timezone config_path
  [ -n "${4:-}" ] && echo '{}' > "$4"          # emulate create_example_config's write
  exit 0
fi
exit 0
STUB

chmod +x "$STUBDIR/git" "$STUBDIR/python3"

# ---------------------------------------------------------------------------
# run_case NAME EXPECTED_EXIT WANT_SUBSTR NOTWANT_SUBSTR [env assignments...]
# ---------------------------------------------------------------------------
run_case() {
  local name="$1" want_exit="$2" want="$3" notwant="$4"; shift 4
  local workdir; workdir="$(mktemp -d)"
  local out rc
  out="$(cd "$workdir" && env PATH="$STUBDIR:$PATH" "$@" bash "$SCRIPT" ./dev_data 5 2>&1)"
  rc=$?
  rm -rf "$workdir"

  local ok=1
  [ "$rc" -eq "$want_exit" ] || { echo "  exit: got $rc want $want_exit"; ok=0; }
  if [ -n "$want" ] && ! grep -qF "$want" <<<"$out"; then
    echo "  missing expected: '$want'"; ok=0
  fi
  if [ -n "$notwant" ] && grep -qF "$notwant" <<<"$out"; then
    echo "  found forbidden: '$notwant'"; ok=0
  fi
  if [ "$ok" -eq 1 ]; then
    echo "PASS: $name"
  else
    echo "FAIL: $name"; echo "----- output -----"; echo "$out"; echo "------------------"
    fails=$((fails + 1))
  fi
}

# ---------------------------------------------------------------------------
# run_case_source NAME EXPECTED_EXIT WANT_SUBSTR CHECK_FILE [env assignments...] -- SCRIPT_ARGS...
#
# Like run_case, but for the --source cases: these need custom flags/positionals
# per case (not the fixed "./dev_data 5"), and some assert a file landed in the
# workdir, so the workdir is kept around until after that check instead of being
# torn down before the caller can see it. CHECK_FILE is a workdir-relative path,
# or "" to skip the file check.
# ---------------------------------------------------------------------------
run_case_source() {
  local name="$1" want_exit="$2" want="$3" checkfile="$4"; shift 4
  local envs=()
  while [ "$1" != "--" ]; do envs+=("$1"); shift; done
  shift # drop the -- separator

  local workdir; workdir="$(mktemp -d)"
  local out rc
  out="$(cd "$workdir" && env PATH="$STUBDIR:$PATH" "${envs[@]+"${envs[@]}"}" bash "$SCRIPT" "$@" 2>&1)"
  rc=$?

  local ok=1
  [ "$rc" -eq "$want_exit" ] || { echo "  exit: got $rc want $want_exit"; ok=0; }
  if [ -n "$want" ] && ! grep -qF "$want" <<<"$out"; then
    echo "  missing expected: '$want'"; ok=0
  fi
  if [ -n "$checkfile" ] && [ ! -f "$workdir/$checkfile" ]; then
    echo "  missing expected file: '$checkfile'"; ok=0
  fi
  rm -rf "$workdir"

  if [ "$ok" -eq 1 ]; then
    echo "PASS: $name"
  else
    echo "FAIL: $name"; echo "----- output -----"; echo "$out"; echo "------------------"
    fails=$((fails + 1))
  fi
}

# A. Happy path: clifpy ok, generation writes files -> ready + exit 0 + provenance SHA.
run_case "happy path prints ready + provenance" 0 "Non-PHI sandbox ready" "NOT ready" \
  STUB_GEN_WRITES_FILES=1

# B. Green-while-red: generation "succeeds" but writes nothing -> NOT ready + exit 2.
run_case "empty generation is not green" 2 "Sandbox NOT ready" "Non-PHI sandbox ready"

# C. Generation fails outright -> NOT ready + exit 2.
run_case "failed generation is not green" 2 "Sandbox NOT ready" "Non-PHI sandbox ready" \
  STUB_FAIL_GEN=1

# D. clifpy missing -> fail fast (exit 2, install hint) BEFORE any clone.
run_case "clifpy preflight fails before clone" 2 "pip install -U clifpy" "Cloning" \
  STUB_FAIL_CLIFPY=1

# D2. clifpy present but too OLD (no create_example_config) -> preflight still
# fails fast before clone, because it imports the exact symbol, not bare clifpy.
run_case "old clifpy without create_example_config fails before clone" 2 "create_example_config" "Cloning" \
  STUB_OLD_CLIFPY=1

# E. Bad pin ref -> loud failure, not a silent run of whatever is checked out.
run_case "unknown pin ref fails loudly" 2 "not found" "Non-PHI sandbox ready" \
  STUB_BAD_REF=nope CLIF_SYNTHETIC_REF=nope

# F. Unsupported CLIF_SCHEMA_VERSION -> reject early, before any clone.
run_case "bad schema version rejected" 2 "unsupported" "Cloning" \
  CLIF_SCHEMA_VERSION=9.9

# G. Unknown --source fails fast, before any clone.
run_case_source "unknown --source fails fast" 2 "unknown --source" "" \
  -- --source not-a-source

# H. clif-forge-sample happy path: copies the committed parquet, no generation.
run_case_source "clif-forge-sample happy path" 0 "sandbox ready" "dev_data/clif_vitals.parquet" \
  STUB_GIT_MAKE_SAMPLE=1 -- --source clif-forge-sample ./dev_data

# I. clif-forge-sample with an EMPTY sample dir never says ready.
run_case_source "empty clif-forge sample dir is not green" 2 "" "" \
  -- --source clif-forge-sample ./dev_data

# J. --config writes the config file at the given path.
run_case_source "--config writes config at given path" 0 "" "custom.json" \
  STUB_GIT_MAKE_SAMPLE=1 -- --source clif-forge-sample --config ./custom.json ./dev_data

echo
if [ "$fails" -eq 0 ]; then
  echo "All setup_dev_data.sh failure-path tests passed."
else
  echo "$fails test case(s) failed."
  exit 1
fi
