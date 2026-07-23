#!/usr/bin/env bash
#
# test_check_clifpy_currency.sh — network-free tests for check_clifpy_currency.sh.
#
# Drives the drift guard against a stubbed upstream clifpy tree via the
# CLIFPY_UPSTREAM_DIR seam (no curl/tar, no network). Each case builds a fresh
# baseline upstream that mirrors the currently-vendored artifacts (so the guard
# reports "ok" everywhere), then mutates it to provoke one outcome and asserts
# the guard's exit status and output.
#
# Run:  bash skills/clif-icu/scripts/tests/test_check_clifpy_currency.sh
# Exit: 0 = all pass, 1 = a case failed.

set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(cd "$TESTS_DIR/.." && pwd)"
SKILL_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
GUARD="$SCRIPTS_DIR/check_clifpy_currency.sh"

pass=0 fail=0

# Build a baseline upstream tree in $1 that mirrors the vendored artifacts,
# so an unmutated run reports "ok" for every file and no advisories.
build_baseline() {
  local up="$1"
  mkdir -p "$up/schemas/2.1" "$up/utils"
  local f b
  for f in "$SKILL_ROOT"/schemas/*.yaml; do
    b="$(basename "$f")"
    case "$b" in
      # Top-level configs live at clifpy/schemas/ (not schemas/2.1/).
      outlier_config.yaml|wide_tables_config.yaml) cp "$f" "$up/schemas/$b" ;;
      *) cp "$f" "$up/schemas/2.1/$b" ;;
    esac
  done
  for f in "$SKILL_ROOT"/reference/clifpy_utils/*.py; do
    b="$(basename "$f")"
    [ "$b" = "__init__.py" ] && continue   # curated; guard skips it
    cp "$f" "$up/utils/$b"
  done
}

# run_case NAME EXPECTED_EXIT WANT_SUBSTR NOTWANT_SUBSTR MUTATOR_FN
run_case() {
  local name="$1" want_exit="$2" want="$3" notwant="$4" mutate="$5"
  local up out rc
  up="$(mktemp -d)"
  build_baseline "$up"
  "$mutate" "$up"                      # apply the scenario's mutation
  set +e
  out="$(CLIFPY_UPSTREAM_DIR="$up" bash "$GUARD" 2>&1)"; rc=$?
  set -e
  rm -rf "$up"

  local ok=1
  [ "$rc" -eq "$want_exit" ] || { ok=0; echo "  exit: got $rc want $want_exit"; }
  if [ -n "$want" ] && ! grep -qF "$want" <<<"$out"; then ok=0; echo "  missing expected: '$want'"; fi
  if [ -n "$notwant" ] && grep -qF "$notwant" <<<"$out"; then ok=0; echo "  found forbidden: '$notwant'"; fi
  if [ "$ok" -eq 1 ]; then echo "PASS: $name"; pass=$((pass + 1))
  else echo "FAIL: $name"; echo "----- output -----"; echo "$out"; echo "------------------"; fail=$((fail + 1)); fi
}

noop() { :; }
mutate_content() { printf '\n# drift\n' >> "$1/schemas/2.1/adt_schema.yaml"; }        # content diff
mutate_orphan()  { rm -f "$1/schemas/2.1/adt_schema.yaml"; }                            # vendored file gone upstream
mutate_new_tbl() { cp "$1/schemas/2.1/adt_schema.yaml" "$1/schemas/2.1/newthing_schema.yaml"; }  # upstream adds a table
mutate_new_util(){ printf 'x = 1\n' > "$1/utils/brand_new_helper.py"; }                 # upstream adds a util

run_case "clean baseline -> no drift"              0 "No drift"     "DRIFT"        noop
run_case "content diff -> DRIFT, exit 1"           1 "DRIFT"        ""             mutate_content
run_case "orphaned vendored file -> NO-UPSTREAM"   1 "NO-UPSTREAM"  ""             mutate_orphan
run_case "new upstream table -> NOTE, exit 0"      0 "NOTE"         "Drift detected" mutate_new_tbl
run_case "new upstream util -> NOTE, exit 0"       0 "NOTE"         "Drift detected" mutate_new_util

echo
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
