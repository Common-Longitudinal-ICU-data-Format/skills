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
  clone)   mkdir -p "$3/.git"; exit 0 ;;      # git clone URL DIR
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
if [ "${1:-}" = "-c" ]; then                   # import clifpy preflight
  [ -n "${STUB_FAIL_CLIFPY:-}" ] && exit 1
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
  cat >/dev/null; exit 0
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

# A. Happy path: clifpy ok, generation writes files -> ready + exit 0 + provenance SHA.
run_case "happy path prints ready + provenance" 0 "Non-PHI sandbox ready" "NOT ready" \
  STUB_GEN_WRITES_FILES=1

# B. Green-while-red: generation "succeeds" but writes nothing -> NOT ready + exit 2.
run_case "empty generation is not green" 2 "Sandbox NOT ready" "Non-PHI sandbox ready"

# C. Generation fails outright -> NOT ready + exit 2.
run_case "failed generation is not green" 2 "Sandbox NOT ready" "Non-PHI sandbox ready" \
  STUB_FAIL_GEN=1

# D. clifpy missing -> fail fast (exit 2, install hint) BEFORE any clone.
run_case "clifpy preflight fails before clone" 2 "pip install clifpy" "Cloning" \
  STUB_FAIL_CLIFPY=1

# E. Bad pin ref -> loud failure, not a silent run of whatever is checked out.
run_case "unknown pin ref fails loudly" 2 "not found" "Non-PHI sandbox ready" \
  STUB_BAD_REF=nope CLIF_SYNTHETIC_REF=nope

echo
if [ "$fails" -eq 0 ]; then
  echo "All setup_dev_data.sh failure-path tests passed."
else
  echo "$fails test case(s) failed."
  exit 1
fi
