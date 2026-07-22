---
title: Refresh clifpy_utils Reference Against clifpy 0.5.0 - Plan
type: fix
date: 2026-07-22
product_contract_source: ce-plan-bootstrap
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
---

# Refresh clifpy_utils Reference Against clifpy 0.5.0 - Plan

## Goal Capsule

- **Objective:** Bring `skills/clif-icu/reference/clifpy_utils/` back into sync with clifpy's current `v0.5.0` release, and correct the accompanying reference docs to match.
- **Authority hierarchy:** This plan's Key Technical Decisions govern file-by-file scope. Where a vendored file's content conflicts with this plan, the pinned upstream `v0.5.0` source is authoritative for what to copy; this plan is authoritative for which files to touch and how to describe them.
- **Stop conditions:** Stop and raise a question if a vendored file's `v0.5.0` source imports from one of the 8 out-of-scope new modules (ase, crosswalk, rule_codes, migrate_versions_2_1_to_3, report_generator, io_polars, datetime_polars, sofa_polars) in a way that breaks it as a standalone reference — this plan verified no such dependency exists for the in-scope files as of `v0.5.0`, so a real one would mean upstream moved further and the diff needs to be redone.
- **Execution profile:** Small, bounded, single-package content refresh. No runtime application, no test harness in this repo — verification is diff-review against the pinned upstream tag.
- **Tail ownership:** The implementer opens or extends a PR against `Common-Longitudinal-ICU-data-Format/skills` the same way PR #1 did (fork remote, feature branch, PR to upstream `main`).

---

## Product Contract

### Summary

Refresh the 14 vendored `.py` files under `skills/clif-icu/reference/clifpy_utils/` to match clifpy's `v0.5.0` release, and update `clifpy_functions.md` / `configuration.md` so the accompanying descriptions match the refreshed code. This is the follow-up item PR #1 flagged in its test plan. New upstream modules in `v0.5.0` that aren't currently vendored stay out of scope for this pass; they get a short pointer note instead.

### Problem Frame

PR #1 fixed the skill's stale version claims and metadata, but its own test plan flagged that `reference/clifpy_utils/*.py` was only corrected in the docs describing it, not re-vendored. Diffing every local file against the `v0.5.0` tag confirms the gap is real: `validator.py` alone grew from 1,889 to 7,398 lines as clifpy added a full data-quality-assessment (DQA) framework (`run_full_dqa`, the `check_*` conformance/completeness/relational-integrity functions), `io.py` gained a `LazyRelation`/DuckDB lazy-loading path, and `comorbidity.py`, `config.py`, `logging_config.py`, `wide_dataset.py` picked up smaller behavioral changes. Seven files (`mdro_flags.py`, `outlier_handler.py`, `query.py`, `sofa.py`, `stitching_encounters.py`, `unit_converter.py`, `waterfall.py`) are already byte-identical to `v0.5.0` and need no change. Left as-is, an agent using this skill for DQA or lazy-loading guidance would be reading function names and signatures that no longer match the installed package — the same failure mode PR #1 corrected for the data-dictionary docs, now recurring one layer down in the vendored source itself.

### Requirements

- R1. Every vendored `.py` file in `reference/clifpy_utils/` matches its `v0.5.0` upstream counterpart, or is confirmed already identical, except `__init__.py`, which mirrors `v0.5.0` minus the two import blocks for the out-of-scope `ase` and `report_generator` modules (see Key Technical Decisions).
- R2. `clifpy_functions.md` and `configuration.md` describe the refreshed function set accurately, including the new `clif_version` config field and the current DQA entry points in `validator.py`.
- R3. The 8 upstream modules new in `v0.5.0` (ASE sepsis calculator, CLIF 2.1->3.0 crosswalk/migration tooling, DQA rule codes, PDF/CSV report generation, and the three polars-native performance variants) are referenced by name with a pointer to upstream, not vendored, in this pass.
- R4. PR #1's staleness disclaimer in `clifpy_functions.md` (which warned that `validator.py` predated the DQA framework) is corrected once `validator.py` itself is current, so the skill doesn't carry a stale warning about itself.

### Scope Boundaries

#### Deferred to Follow-Up Work

- Vendoring the 8 new upstream modules (`ase.py`, `crosswalk.py`, `rule_codes.py`, `migrate_versions_2_1_to_3.py`, `report_generator.py`, `io_polars.py`, `datetime_polars.py`, `sofa_polars.py`) if the skill's scope is later expanded to cover sepsis surveillance, CLIF v3.0 migration tooling, or a polars-native performance path. `report_generator.py` would also add a new `reportlab` dependency to the skill's Requirements section.
- Any automated mechanism (CI check, periodic script) to detect future drift between this vendored snapshot and clifpy's latest release — this plan is a one-time manual refresh, not a standing sync process.

#### Outside This Work's Identity

- Running an actual CLIF 2.1->3.0 data migration. `crosswalk.py` and `migrate_versions_2_1_to_3.py` are upstream tooling being referenced, not executed here.

---

## Planning Contract

### Key Technical Decisions

- **Scope limited to the 14 already-vendored files.** Confirmed with the user: this pass refreshes existing content rather than expanding the skill to cover the 8 new upstream modules. Keeps the skill's footprint tied to its stated purpose (CLIF table loading, filtering, clinical scoring, wide datasets) and avoids adding the `reportlab` dependency `report_generator.py` would require.
- **`validator.py` vendored in full, not curated.** Confirmed with the user: the file is copied verbatim from `v0.5.0` (1,889 -> 7,398 lines) for consistency with how every other file in the folder is treated. Under the standard Claude Skills progressive-disclosure model, only `SKILL.md` loads at session start; files under `reference/` (including this one) load on demand when an agent opens them, so this file's size is a repo-size consideration, not a per-session context-cost one, unless a future skill revision changes that loading behavior.
- **`__init__.py` mirrors only the vendored files' exports.** Upstream `v0.5.0`'s `__init__.py` also imports `from .ase import compute_ase` and a `from .report_generator import (...)` block. Since those two modules are out of scope (KTD 1), the refreshed `__init__.py` drops those two import blocks and their `__all__` entries rather than copying them verbatim — otherwise the file would reference modules this folder doesn't contain. Verified: `validator.py`'s DQA imports (`run_full_dqa`, the `check_*` family, `DQAConformanceResult`, etc.) have no dependency on `rule_codes.py` or `report_generator.py`, so the DQA import block copies over cleanly.
- **Source of truth is the `v0.5.0` git tag, not `main`.** Pins the refresh to the exact release `SKILL.md` already cites (from PR #1), keeping that version-pin claim accurate rather than drifting ahead of it.
- **`comorbidity.py`'s ICD-10 matching change is a real bug fix, not cosmetic case-normalization.** The old code (`str.to_uppercase().str.split(".").list.get(0)`) discards everything after the *first* period, not just the period character: `"I25.2"` becomes `"I25"`. `v0.5.0`'s code (`str.to_lowercase().str.replace_all(".", "")`) keeps the sub-decimal digit: `"I25.2"` becomes `"i252"`. This matters because CCI's `myocardial_infarction` condition list is `["I21", "I22", "I252"]` (confirmed in `clifpy/data/comorbidity/cci.yaml` at `v0.5.0`) — the old logic's truncated `"I25"` never matches the `starts_with("I252")` check, so a patient with diagnosis code `"I25.2"` was silently excluded from the `myocardial_infarction` CCI flag; the new logic correctly matches it. The same undercounting risk applies to every condition whose code list includes a code more specific than its 3-character category (e.g., `diabetes_uncomplicated`'s `E100`-`E149` codes). U1 vendors this fix as-is (it's a correctness improvement upstream already made and verified), but must test with a sub-decimal-precision diagnosis code, not just a category-level one — see U1's test scenarios.

### Assumptions

- Implementation continues on the existing `update-clif-2.1.0-currency` branch / PR #1 (fork remote `fork` -> `sajor2000/skills`, PR against `Common-Longitudinal-ICU-data-Format/skills`), rather than opening a second PR, since this is a direct continuation of PR #1's own noted follow-up. Low-stakes to change if the maintainer prefers a separate PR.

### Risks & Dependencies

- **Drift will recur.** Nothing in this plan prevents `clifpy_utils/*.py` from going stale again after clifpy's next release; this is a one-time refresh (see Scope Boundaries). Acceptable given the repo has no CI to enforce a sync check today.
- **`io.py`'s new `lazy=True` path depends on the installed `duckdb` package's relational API.** Low risk here specifically because this is reference material read by an agent, not code executed in this repo — inaccuracy would surface as a documentation error, not a runtime break.
- **The refresh introduces a new cross-reference to `clifpy/schemas`.** Neither file has any relative import today, but `v0.5.0`'s `validator.py` adds `from ..schemas import DEFAULT_CLIF_VERSION, load_schema` and `config.py` adds `from ..schemas import DEFAULT_CLIF_VERSION`. This package-level module isn't one of the 8 out-of-scope modules and isn't vendored here; U4 adds a one-line pointer in `clifpy_functions.md` noting `DEFAULT_CLIF_VERSION`/`load_schema` come from clifpy's core `schemas` module rather than being undefined names.

### Sources & Research

- `Common-Longitudinal-ICU-data-Format/clifpy` GitHub repo, tag `v0.5.0` — every file under `clifpy/utils/` fetched via the GitHub Contents API and diffed directly against the corresponding local file on 2026-07-22.
- PR #1 (`Common-Longitudinal-ICU-data-Format/skills#1`) — originating follow-up note in its test plan.

---

## Implementation Units

### U1. Refresh drop-in files with small, clean diffs

**Goal:** Replace `comorbidity.py`, `config.py`, `logging_config.py`, and `wide_dataset.py` with their `v0.5.0` source; confirm the 7 byte-identical files need no change.

**Requirements:** R1

**Dependencies:** None

**Files:**
- `skills/clif-icu/reference/clifpy_utils/comorbidity.py`
- `skills/clif-icu/reference/clifpy_utils/config.py`
- `skills/clif-icu/reference/clifpy_utils/logging_config.py`
- `skills/clif-icu/reference/clifpy_utils/wide_dataset.py`

**Approach:** Straight copy from the `v0.5.0` tag for each of the four files. No content curation needed — each diff is small and self-contained (ICD-10 matching fix in `comorbidity.py`, see Key Technical Decisions; a new `clif_version` field in `config.py`; log file mode changed from overwrite to append in `logging_config.py`; a versioned schema path in `wide_dataset.py`'s docstring). Confirm `mdro_flags.py`, `outlier_handler.py`, `query.py`, `sofa.py`, `stitching_encounters.py`, `unit_converter.py`, and `waterfall.py` are still byte-identical to `v0.5.0` at implementation time (re-diff, since time will have passed since this plan's research). If any of the 7 has diverged, add it to this unit's Files list and vendor it the same way as the other four; if still identical, leave it untouched.

**Test scenarios:**
- Verify `comorbidity.py`'s corrected matching against at least one sub-decimal-precision diagnosis code per affected condition, not just a category-level code — e.g., diagnosis `"I25.2"` must set the `myocardial_infarction` CCI flag `True` (its condition list is `["I21", "I22", "I252"]`; the pre-`v0.5.0` code would truncate `"I25.2"` to `"I25"` and miss the `I252` match). Confirm the flag was `False` under the old logic and `True` under the new logic for this input, then repeat with one more affected condition (e.g., `diabetes_uncomplicated`'s `E100`-`E149` codes) to confirm the pattern generalizes.
- Confirm `config.py`'s `create_example_config()` still produces valid JSON/YAML including the new `clif_version` field, and that `load_config()` / `get_config_or_params()` still parse a config file without the field (backward compatible with existing configs).
- Test expectation: none -- `logging_config.py`'s append-vs-overwrite change and `wide_dataset.py`'s docstring path update are non-behavioral for this reference material; confirm by reading the diff, no functional check needed.

**Verification:** For each file, `diff <(gh api "repos/Common-Longitudinal-ICU-data-Format/clifpy/contents/clifpy/utils/<file>?ref=v0.5.0" --jq '.content' | base64 -d) skills/clif-icu/reference/clifpy_utils/<file>` shows no output.

---

### U2. Refresh io.py and curate __init__.py

**Goal:** Vendor `io.py`'s new `LazyRelation` class, `lazy=True` parameter on `load_data`/`load_parquet_with_tz`, and the `fetch_lazy_result`/`close_lazy_relation` helpers. Refresh `__init__.py` to mirror `v0.5.0`'s export list minus the `ase` and `report_generator` import blocks (KTD: `__init__.py` mirrors only the vendored files' exports).

**Requirements:** R1

**Dependencies:** U1 (establishes the "vendor as-is" pattern this unit deviates from for `__init__.py`)

**Files:**
- `skills/clif-icu/reference/clifpy_utils/io.py`
- `skills/clif-icu/reference/clifpy_utils/__init__.py`

**Approach:** `io.py` copies straight from `v0.5.0`. `__init__.py` starts from the `v0.5.0` source, then removes the `from .ase import compute_ase` line and the `from .report_generator import (...)` block (and their corresponding `__all__` entries), leaving every other import — including the DQA imports from `.validator` — intact, since those have no dependency on the two excluded modules.

**Test scenarios:**
- Confirm every name imported in the curated `__init__.py` corresponds to a symbol actually defined in one of the 14 vendored files (spot-check `run_full_dqa`, `check_required_columns`, `LazyRelation`, `fetch_lazy_result` against `validator.py` / `io.py`).
- Confirm no import line in the curated `__init__.py` references `.ase` or `.report_generator`.
- Re-check at implementation time (not just recall this plan's research) that upstream `__init__.py` still imports only `.ase` and `.report_generator` among the 8 out-of-scope modules — if a 9th module has been added to `__init__.py` since, exclude it the same way.

**Verification:** `grep -n "ase\|report_generator" skills/clif-icu/reference/clifpy_utils/__init__.py` returns no matches. `diff <(gh api ".../clifpy/utils/io.py?ref=v0.5.0" ...) skills/clif-icu/reference/clifpy_utils/io.py` shows no output.

---

### U3. Vendor validator.py in full

**Goal:** Replace `validator.py` with the full `v0.5.0` source (1,889 -> 7,398 lines), bringing in the DQA framework (`run_full_dqa`, `run_conformance_checks`, `run_completeness_checks`, `run_relational_integrity_checks`, the `check_*` family, `DQAConformanceResult`/`DQACompletenessResult`).

**Requirements:** R1, R4

**Dependencies:** None

**Files:**
- `skills/clif-icu/reference/clifpy_utils/validator.py`

**Approach:** Straight copy from the `v0.5.0` tag. Already verified this file has zero references to `rule_codes` or `report_generator` (its only relative import is `from ..schemas import DEFAULT_CLIF_VERSION, load_schema`, a package-level module outside `clifpy_utils`), so it stays self-contained despite the two excluded sibling modules.

**Test scenarios:**
- Confirm the vendored file still has zero references to `rule_codes` or `report_generator` (re-check at implementation time in case upstream added a dependency since this plan's research).
- Confirm the file's only relative import remains `from ..schemas import ...`.

**Verification:** `grep -c "rule_codes\|report_generator" skills/clif-icu/reference/clifpy_utils/validator.py` returns `0`. `diff` against the pinned `v0.5.0` source shows no output.

---

### U4. Update accompanying docs and resolve the PR #1 staleness note

**Goal:** Update `clifpy_functions.md` and `configuration.md` to describe the refreshed files accurately, replace PR #1's now-resolved staleness disclaimer with a short pointer note about the 8 out-of-scope new modules, and bump `marketplace.json`'s metadata version.

**Requirements:** R2, R3, R4

**Dependencies:** U1, U2, U3 (describes their output)

**Files:**
- `skills/clif-icu/reference/clifpy_utils/clifpy_functions.md`
- `skills/clif-icu/reference/clifpy_utils/configuration.md`
- `.claude-plugin/marketplace.json`

**Approach:** In `clifpy_functions.md`: replace the PR #1 staleness note (which said `validator.py` predated the DQA framework) with a short note that `clifpy_utils/` now mirrors `v0.5.0` in full for the 14 files it contains, plus a one-line-per-module pointer to the 8 modules deliberately left unvendored (name each, one clause on what it does, link to the upstream `clifpy/utils/` path), plus a one-line pointer that `DEFAULT_CLIF_VERSION`/`load_schema` (referenced by the refreshed `validator.py`/`config.py`) come from clifpy's core `schemas` module, not vendored here. Update the `io.py` row/description to mention the lazy-loading path and the `comorbidity.py` row/description to mention the ICD sub-decimal-precision fix. In `configuration.md`: add the new `clif_version` field to the Optional Fields table. In `marketplace.json`: bump the metadata version (1.2.0 -> 1.2.1).

**Test scenarios:**
- Confirm `clifpy_functions.md` no longer claims `validate_table()` / `verify_column_dtypes()` are current API without qualification (superseded by the `v0.5.0` refresh in U3).
- Confirm the 8 out-of-scope modules are each named once with a one-clause description, not silently omitted.
- Confirm `DEFAULT_CLIF_VERSION`/`load_schema` have a one-line pointer explaining they come from clifpy's core `schemas` module.
- Test expectation: none -- the `marketplace.json` version bump has no behavior to verify beyond the value changing.

**Verification:** Read `clifpy_functions.md` and `configuration.md` end to end and confirm every code-level claim matches the U1-U3 file contents; `jq .metadata.version .claude-plugin/marketplace.json` shows the bumped value.

---

## Verification Contract

This repo has no test framework or CI (confirmed: no `.github/`, no `package.json`, no `pytest.ini`). Verification is diff-review against the pinned upstream tag plus manual read-through of the updated docs.

| Check | Command / Action | Applies to |
|---|---|---|
| Vendored file matches `v0.5.0` | `diff <(gh api "repos/Common-Longitudinal-ICU-data-Format/clifpy/contents/clifpy/utils/<file>?ref=v0.5.0" --jq '.content' \| base64 -d) skills/clif-icu/reference/clifpy_utils/<file>` shows no output | U1, U2 (`io.py`), U3 |
| `__init__.py` has no reference to excluded modules | `grep -n "ase\|report_generator" skills/clif-icu/reference/clifpy_utils/__init__.py` returns no matches | U2 |
| `validator.py` stays self-contained | `grep -c "rule_codes\|report_generator" skills/clif-icu/reference/clifpy_utils/validator.py` returns `0` | U3 |
| Docs describe the refreshed code accurately | Manual read-through of `clifpy_functions.md` and `configuration.md` against the U1-U3 file contents | U4 |

## Definition of Done

- All 4 units complete; every vendored `.py` file in `skills/clif-icu/reference/clifpy_utils/` either matches `v0.5.0` byte-for-byte or (for `__init__.py`) matches it minus the two deliberately-excluded import blocks.
- `clifpy_functions.md` and `configuration.md` reflect the refreshed files, including the new `clif_version` field and a pointer note for the 8 out-of-scope modules.
- The PR #1 staleness disclaimer about `validator.py` is removed or rewritten to reflect that the file is now current.
- `marketplace.json` metadata version is bumped.
- No leftover reference to `ase` or `report_generator` in any vendored `.py` file.
