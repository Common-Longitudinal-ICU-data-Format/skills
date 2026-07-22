---
title: Refresh vendored schemas, fix example-script API drift, and guard against future clifpy drift
date: 2026-07-22
type: fix
origin: follow-up to docs/plans/2026-07-22-001-fix-refresh-clifpy-utils-reference-plan.md
status: shipped
---

# Refresh schemas + scripts + currency guard

## Goal Capsule

Extend the clifpy 0.5.0 currency work (which covered `reference/clifpy_utils/*.py`)
to the skill's two other vendored clifpy artifacts — the `schemas/*.yaml` table
definitions and the `scripts/*.py` examples — and add a mechanism that prevents
all three from silently going stale after clifpy's next release.

## Findings (verified 2026-07-22)

Ground truth: clifpy `v0.5.0` tarball (`clifpy/schemas/2.1/`, `clifpy/utils/`,
`clifpy/clif_orchestrator.py`); the main CLIF repo mCIDE.

| Area | Status | Fix |
|------|--------|-----|
| `schemas/*.yaml` (18 table schemas) | All drifted from clifpy 0.5.0 | Re-vendor verbatim (U1) |
| `schemas/outlier_config.yaml`, `wide_tables_config.yaml` | Byte-identical | none |
| `mCIDE/*.csv` (clifpy-enumerable lists) | Exact match to 0.5.0 schemas | none (verified) |
| `mCIDE/*.csv` (organisms, susceptibility, code_status, crrt modes, routes, procedures, invasive_hemodynamics, key_icu_orders) | Not enumerated by clifpy; authority is main CLIF repo | out of scope; documented |
| `scripts/sofa_score_calculation.py` | All 0.5.0 API calls valid | none |
| `scripts/cohort_identification_example.py` | `load_table(..., categories=[...])` invalid kwarg → `TypeError` | fix to `filters=` (U2) |
| Drift recurrence | No guard | add currency script (U3) |

Schema drift was substantive, not cosmetic:
- **labs**: reference-units block restructured into `reference_units` (canonical
  key) + new `allowed_unit_variants` (accepted spellings) — +363 upstream lines.
- **respiratory_support**: `required_columns` narrowed — 7 columns dropped from
  the mandatory list, so the stale schema raised false "missing required column"
  validation errors.
- **hospitalization**: new `fips_version` column.
- **medication_admin_continuous**: epoprostenol now maps to IV + inhaled groups —
  the skill's own `#to fix multi mapping` TODO, resolved upstream.
- `version: "2.1"` field, `allow_missing` flags, and `birth_date` DATE (was
  DATETIME) added across schemas.

## Implementation Units

- **U1** — Re-vendor 18 table schema YAMLs verbatim from `clifpy/schemas/2.1/`
  (v0.5.0). Verify byte-identical. Leave the two already-identical config YAMLs.
- **U2** — Fix `load_table('vitals', ..., categories=['weight_kg'])` →
  `filters={'vital_category': ['weight_kg']}` in the cohort example. SOFA script
  needs no change (verified all kwargs against `clif_orchestrator.py`).
- **U3** — Add `scripts/check_clifpy_currency.sh`: downloads a pinned clifpy tag,
  diffs vendored `schemas/*.yaml` and `reference/clifpy_utils/*.py` against
  upstream, exits non-zero on drift. `__init__.py` skipped (curated).
- **U4** — Docs: schema provenance + currency note in SKILL.md, mCIDE currency
  note, currency-script usage; bump marketplace to 1.2.2; this plan doc.

## Verification

- U1: `diff -q` of all 18 files against v0.5.0 → all identical; `check_clifpy_currency.sh` → 0 drift, exit 0.
- U2: `grep categories= scripts/` → none; all remaining `load_table` calls use valid kwargs.
- U3: script run against v0.5.0 → all 20 schema files + 13 util modules `ok`, exit 0.

## Scope Boundaries

- No CLIF v3.0 content (still prerelease-only).

## Follow-up: v2.1.1 adoption (same day)

After shipping U1–U4, verification against the main CLIF repo revealed that
**v2.1.1** — not v2.1.0 — is the latest non-prerelease CLIF release (published
2026-01-02; v3.0.0 and v2.2.0 remain prereleases, v2.2.0 marked OBSOLETE). The
skill's target was bumped to v2.1.1:

- Re-vendored the two mCIDE files that v2.1.1 patched from the main CLIF repo at
  tag `v2.1.1`: `labs/clif_lab_categories.csv` (descriptive `notes` column moved
  to end, `lab_order_category` regroupings) and
  `microbiology_culture/clif_microbiology_culture_organism_categories.csv`
  (removed misspelled `citrobacter_koserii`, de-duplicated
  `clostridium_difficile` into `clostridioides_difficile`). All other 35 mCIDE
  files were already byte-identical to v2.1.1.
- v2.1.1 changed only descriptive/grouping columns and de-duplication; the
  `*_category` value lists are **unchanged** from v2.1.0, so clifpy 0.5.0's `2.1`
  schemas still validate v2.1.1 data — the re-vendored schemas need no change.
- Updated version claims in `SKILL.md` and the `mCIDE/README.md` currency note;
  bumped marketplace to 1.2.3.

## Follow-up: CI drift guard (same day)

The currency script is now wired into CI at
`.github/workflows/clifpy-currency.yml` — it runs on pushes/PRs that touch the
vendored `schemas/`, `reference/clifpy_utils/`, or the script itself, plus a
weekly cron (Mondays 06:00 UTC) so a new clifpy release surfaces drift even
when nobody edits those files. `workflow_dispatch` accepts an optional
`clifpy_tag` to preview drift a bump would introduce.
