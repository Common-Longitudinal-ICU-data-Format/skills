#!/usr/bin/env bash
#
# check_clifpy_currency.sh — detect drift between this skill's vendored
# clifpy artifacts and a pinned clifpy release.
#
# The clif-icu skill vendors two kinds of clifpy artifacts that must stay
# in sync with a specific clifpy release:
#   1. schemas/*.yaml            <- clifpy/schemas/2.1/*.yaml (+ two top-level configs)
#   2. reference/clifpy_utils/*.py <- clifpy/utils/*.py  (verbatim, except __init__.py)
#
# These drift silently whenever clifpy ships a new release. Run this script
# after a clifpy release (or in CI) to see exactly which vendored files have
# fallen behind. It does NOT modify anything — it only reports.
#
# Usage:
#   scripts/check_clifpy_currency.sh [CLIFPY_TAG]
#
#   CLIFPY_TAG defaults to the PINNED_VERSION below — the release this skill
#   currently claims to mirror. Pass a newer tag (e.g. v0.6.0) to preview the
#   drift a bump would introduce.
#
# What counts as drift (non-zero exit):
#   DRIFT        a vendored file's contents differ from its upstream twin.
#   NO-UPSTREAM  a vendored file no longer maps to any upstream file (renamed,
#                removed, or restructured upstream) — a hard failure, since a
#                vendored artifact with no upstream source is stale by definition.
#
# What is advisory only (does NOT change the exit status):
#   NOTE         an upstream file that is not vendored locally. The vendored set
#                is a CURATED SUBSET (a fixed list of table schemas + a few utils,
#                not a full mirror), so an un-vendored upstream file may be a new
#                table worth adopting OR a helper deliberately left out. The guard
#                cannot tell these apart offline, so it reports them loudly for a
#                human to triage rather than failing CI on an intentional omission.
#
# Exit status: 0 = no drift, 1 = drift/orphan detected, 2 = setup/tooling error.

set -euo pipefail

# The clifpy release this skill currently vendors. Bump this (and re-vendor)
# when moving the skill to a newer clifpy.
PINNED_VERSION="v0.5.0"

CLIFPY_TAG="${1:-$PINNED_VERSION}"
REPO="Common-Longitudinal-ICU-data-Format/clifpy"

# Resolve skill root relative to this script (scripts/ -> skill root).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Comparing vendored artifacts against clifpy $CLIFPY_TAG (pinned: $PINNED_VERSION)"

# Test seam: point CLIFPY_UPSTREAM_DIR at an already-extracted clifpy/ tree to
# diff against it offline (skips the download). Used by the network-free test
# suite; unset in normal runs, which download the pinned tag from GitHub.
if [ -n "${CLIFPY_UPSTREAM_DIR:-}" ]; then
  UP="$CLIFPY_UPSTREAM_DIR"
  [ -d "$UP" ] || { echo "error: CLIFPY_UPSTREAM_DIR '$UP' is not a directory" >&2; exit 2; }
  echo "Using local upstream tree: $UP (download skipped)"
else
  command -v curl >/dev/null 2>&1 || { echo "error: curl not found" >&2; exit 2; }
  command -v tar  >/dev/null 2>&1 || { echo "error: tar not found"  >&2; exit 2; }

  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT

  echo "Downloading clifpy $CLIFPY_TAG ..."
  if ! curl -fsSL "https://github.com/$REPO/archive/refs/tags/$CLIFPY_TAG.tar.gz" -o "$TMP/clifpy.tgz"; then
    echo "error: could not download clifpy tag '$CLIFPY_TAG' (does it exist?)" >&2
    exit 2
  fi
  tar xzf "$TMP/clifpy.tgz" -C "$TMP"
  UP="$(find "$TMP" -maxdepth 1 -type d -name 'clifpy-*' | head -n1)/clifpy"
  [ -d "$UP" ] || { echo "error: unexpected clifpy archive layout" >&2; exit 2; }
fi

drift=0
notes=0

report() { # $1=status  $2=path
  case "$1" in
    DRIFT|NO-UPSTREAM) drift=1 ;;    # content drift or an orphaned vendored file: hard fail
    NOTE)              notes=$((notes + 1)) ;;  # advisory only; never flips the exit status
  esac
  printf '  [%-11s] %s\n' "$1" "$2"
}

echo
echo "== schemas/*.yaml  vs  clifpy/schemas/{2.1,.}/ =="
for f in "$SKILL_ROOT"/schemas/*.yaml; do
  b="$(basename "$f")"
  if   [ -f "$UP/schemas/2.1/$b" ]; then u="$UP/schemas/2.1/$b"
  elif [ -f "$UP/schemas/$b" ];     then u="$UP/schemas/$b"
  else report "NO-UPSTREAM" "$b"; continue
  fi
  if diff -q "$f" "$u" >/dev/null; then report "ok" "$b"; else report "DRIFT" "$b"; fi
done

echo
echo "== reference/clifpy_utils/*.py  vs  clifpy/utils/  (verbatim; __init__.py is curated) =="
for f in "$SKILL_ROOT"/reference/clifpy_utils/*.py; do
  b="$(basename "$f")"
  if [ "$b" = "__init__.py" ]; then report "skip" "$b (curated export list)"; continue; fi
  u="$UP/utils/$b"
  if [ ! -f "$u" ]; then report "NO-UPSTREAM" "$b"; continue; fi
  if diff -q "$f" "$u" >/dev/null; then report "ok" "$b"; else report "DRIFT" "$b"; fi
done

# Reverse pass: surface upstream files this skill does NOT vendor. The forward
# passes only walk vendored files, so without this the guard is blind to tables
# or utils a new clifpy release ADDS. These are advisory (NOTE) — see header.
shopt -s nullglob

echo
echo "== clifpy $CLIFPY_TAG table schemas not vendored locally (advisory) =="
for u in "$UP"/schemas/2.1/*_schema.yaml; do
  b="$(basename "$u")"
  [ -f "$SKILL_ROOT/schemas/$b" ] || report "NOTE" "$b (present upstream, not vendored — new table?)"
done

echo
echo "== clifpy $CLIFPY_TAG utils not vendored locally (advisory) =="
for u in "$UP"/utils/*.py; do
  b="$(basename "$u")"
  [ "$b" = "__init__.py" ] && continue
  [ -f "$SKILL_ROOT/reference/clifpy_utils/$b" ] || report "NOTE" "$b (present upstream, not vendored)"
done

shopt -u nullglob

echo
if [ "$drift" -eq 0 ]; then
  echo "No drift: vendored artifacts match clifpy $CLIFPY_TAG."
else
  echo "Drift detected. For DRIFT files, re-vendor from clifpy $CLIFPY_TAG, e.g.:"
  echo "  gh api \"repos/$REPO/contents/clifpy/schemas/2.1/<file>?ref=$CLIFPY_TAG\" --jq .content | base64 -d > schemas/<file>"
  echo "then update PINNED_VERSION in this script if you are moving to a new release."
  echo "For NO-UPSTREAM files, the upstream source was renamed/removed — reconcile the"
  echo "vendored copy against clifpy $CLIFPY_TAG (re-point, rename, or drop it)."
fi
if [ "$notes" -gt 0 ]; then
  echo
  echo "Advisory: $notes upstream file(s) above are not vendored (NOTE). This does not"
  echo "fail the check — triage each as a new artifact to adopt or an intentional omission."
fi
exit "$drift"
