# clif-bench

`clif-bench` is a golden-task benchmark harness for the `clif-icu` skill, running
against pinned, synthetic (non-PHI) CLIF data. It serves three purposes:

1. **CI for the skill** — a regression check that skill-authored guidance still
   produces correct aggregate answers as clifpy/the skill evolve.
2. **A citable correctness benchmark** — an agent (or a human) is scored against
   an independently-computed ground truth on well-defined aggregate questions,
   so "the skill helps" is a number, not a vibe.
3. **An extensible template** — new tasks (T02–T10, or site-specific tasks) drop
   into `bench/tasks/` following the same contract described below.

## Task contract

Every task directory `bench/tasks/T##_<slug>/` contains:

- `prompt.md` — the question, exactly as an agent under test would see it. No
  scoring hints, no "gotcha" explanations — those live in this README instead
  (see [T08](#t08-category-trap) below).
- `solution.py` — a reference implementation exposing
  `solve(config_path: str) -> dict`. `config_path` points at a clifpy-compatible
  `config.json`. The returned dict contains **aggregates only** — counts,
  percentages, rates. Never row-level records or ID lists (these are synthetic
  data, but the contract is written as if it were real PHI, since tasks get
  copied as a template).
- `expected.json` — generated (not hand-written) ground truth, committed to the
  repo. Regenerate with `generate_truth.py` (see below); never hand-edit.

`harness.assert_matches(result, expected)` recursively compares the two dicts:
exact equality for ints/strings, `pytest.approx(rel=1e-4)` for floats, and
**skips any dict key starting with `_`** (e.g. `_clifpy_version`) in both the
key-set comparison and value recursion — solutions/truth may carry provenance
metadata alongside the scored fields without it affecting the match.

## How to run

```bash
bash bench/setup_bench_data.sh      # stand up pinned data in bench/.data (git-ignored)
python3 bench/generate_truth.py     # (maintainer-run) regenerate expected.json for all tasks
cd bench && python3 -m pytest test_bench.py -v
```

Expected result: all 10 tasks (`T01`–`T10`) `PASSED`.
`bench/setup_bench_data.sh` requires `pandas`, `pyarrow`, and `clifpy`
(`python3 -m pip install --user pandas pyarrow clifpy` if missing) plus network
access to `github.com` to clone clif-forge.

**Python version (added for T02–T10, 2026-07-31)**: `clifpy==0.5.0`
requires **Python 3.10+**. Its `utils/unit_converter.py` does
`from types import NoneType`, which only exists in the stdlib `types`
module from 3.10 onward — under Python 3.9 (e.g. macOS's
`/usr/bin/python3` / Command Line Tools Python), any solution that imports
`ClifOrchestrator` (`T05`, `T07`) fails at import time with
`ImportError: cannot import name 'NoneType'`. Separately, `clifpy`'s SOFA
utility (`utils/sofa.py`) uses DuckDB's colon-alias `SELECT col: expr`
syntax, which requires `duckdb >= 1.x` — the `duckdb==0.10.2` version that
was resolvable at the time `T01`/`T08` were built raises
`ParserException: syntax error at or near ":"` on that syntax. Run
`bench/`'s commands with a Python 3.10+ interpreter that has
`pandas`, `pyarrow`, `clifpy`, `pyyaml`, and `duckdb>=1.0` installed (e.g.
a throwaway venv built from `python3.10 -m venv`); do not rely on the
system `python3` if it resolves to 3.9.

## How to score an agent

1. Give the agent **only** `bench/tasks/T##_*/prompt.md` and the bench config
   path (`bench/.data/config.json`) — never `solution.py` or `expected.json`.
2. Have the agent write its own `solution.py` implementing
   `solve(config_path: str) -> dict` into the task directory (or a scratch copy
   of it), and drop it in place of the reference solution.
3. Run `cd bench && python3 -m pytest test_bench.py -v`.
4. Report **N passed / N total**. Run once with the `clif-icu` skill available
   to the agent and once without (raw model, no skill) to get a skill-assisted
   vs. raw comparison.

## Pin / provenance

`bench/pin.json` pins the data source:

```json
{
  "source": "clif-forge-sample",
  "repo": "https://github.com/sajor2000/clif-forge",
  "ref": "c29e0e0d101418aa898d0b7daa8250cecd178a3b"
}
```

**Deviation from the original plan**: `clif-forge` has no release tags as of
2026-07-31 (`git tag -l` at that repo is empty; `v0.2.0` does not exist). We
pin to the verified `main` HEAD SHA above instead of a tag — see the `note`
field in `pin.json`. Re-pin to a tag once clif-forge cuts one.

`bench/setup_bench_data.sh` clones clif-forge at that pinned SHA, copies its
committed `sample_dataset/` parquet (`--source clif-forge-sample`, no
generation — fully deterministic), then `subset_bench_data.py` takes the
first 500 `hospitalization_id` (ascending numeric sort) plus their patients —
a fixed, reproducible 500-hospitalization slice, written to `bench/.data/subset`.

clif-forge's own `sample_dataset/manifest.json` (copied alongside the full
sample into `bench/.data/full/`) records per-table row counts and SHA256
checksums for the full 10,000-hospitalization generation
(seed 42, spec `master-sample`), e.g.:

| table | rows | sha256 |
|---|---|---|
| `clif_hospitalization` | 10000 | `5662048a6b4a636d59193a946a2331c45ad7ee6f170f96cf8b5bb00680ebc586` |
| `clif_respiratory_support` | 43057 | `0054f1dffb2a8a3a0f390eff0b00dd215f02f800ff14239cb68ddf92662f4d6b` |
| `clif_crrt_therapy` | 13278 | `c2362a28a09d6487733a566ce0fcbc759a2263b0140a87d1d04287b278b48f5d` |
| `clif_truth` | 2195057 | `b1f7860b25a96ae3bfc281e83eb8b177c4ffbbc8e98a3af6836c4c4777c41db9` |

The bench's own `bench/.data/subset/` (our 500-hospitalization slice) is
git-ignored, not published — the manifest above documents the *source* dataset's
provenance, not a checksum of the subset itself, since the subset is
deterministically re-derivable from the pinned ref by anyone who runs
`setup_bench_data.sh`.

## T08: category trap

`bench/tasks/T08_category_trap/prompt.md` deliberately does not explain why the
task is interesting — an agent under test should not get a hint. This extends
to the prompt's own title: an earlier draft titled the prompt
"High-flow nasal cannula usage (category-convention trap)", which leaked the
trap to the scored agent via the H1 itself (an agent reading its own task
title before reasoning about the query would see "trap" and go looking for
one). The committed `prompt.md` title is the neutral
"High-flow nasal cannula and invasive ventilation usage" — plainly descriptive
of the question asked, with neither "trap" nor "convention" appearing
anywhere in the file. The task **directory** name `T08_category_trap/` still
names the trap (for maintainers browsing `bench/tasks/`), which is fine: per
"How to score an agent" above, a scored agent is only ever given the contents
of `prompt.md`, never the directory name or path components. The trap: this
dataset is CLIF **2.1**, whose `respiratory_support.device_category`
permissible values (`skills/clif-icu/schemas/respiratory_support_schema.yaml`)
are `IMV`, `NIPPV`, `CPAP`, `High Flow NC`, `Face Mask`, `Trach Collar`,
`Nasal Cannula`, `Room Air`, `Other`. CLIF **3.0** renamed several of these
(e.g. lowercase `hfnc` / `imv`-style slugs). An agent that assumes 3.0
conventions and filters on `hfnc` / `imv` (lowercase) will silently get zero
matches — the query runs without error, it just returns wrong (empty)
aggregates. This is exactly the class of silent-wrong-answer failure the skill
is meant to guard against.

**Category-literal verification (mandatory check, done 2026-07-31)**: the
literals used in `solution.py`/`generate_truth.py` (`"High Flow NC"`, `"IMV"`)
were checked against both (a) the actual `device_category` values present in
`bench/.data/subset/clif_respiratory_support.parquet`
(`Nasal Cannula`, `Room Air`, `Face Mask`, `IMV`, `NIPPV`, `High Flow NC` —
`CPAP`, `Trach Collar`, `Other` do not appear in the 500-hospitalization
subset) and (b) `respiratory_support_schema.yaml`'s `permissible_values`. Both
agree exactly with the literals already in the brief — no changes were needed.

**Cross-check against clif-forge's `clif_truth.parquet`** (mandatory,
disagreement reported per instructions, not hidden): `clif_truth.parquet` has
a per-interval `resp_flag` boolean, defined in clif-forge's own source
(`src/clifforge/fit/spine_state.py`) as True when the *latent* per-interval
support state includes `device_category` in
`{High Flow NC, NIPPV, CPAP, IMV}`. In principle, the set of hospitalizations
with `resp_flag == True` at any interval should equal the set of
hospitalizations with a `respiratory_support` row whose `device_category` is
in that same set — same definition, two different tables.

In the 500-hospitalization subset, they do **not** agree:

- Hospitalizations with `resp_flag == True` at any interval (truth table): **255**
- Hospitalizations with a `device_category` in `{High Flow NC, NIPPV, CPAP, IMV}`
  (respiratory_support table): **253**
- Intersection: **144**; only-in-truth: **111**; only-in-respiratory_support: **109**;
  union: **364**

The near-equal totals (255 vs. 253) mask a large symmetric disagreement — only
144 of the 364 hospitalizations touched by either signal agree between the two
tables. Spot-checking individual hospitalizations (e.g. hospitalization_id 9,
10, 16) shows `clif_truth.parquet` marking `resp_flag = True` for intervals
where the corresponding `respiratory_support` rows for that hospitalization
only contain low-flow devices (`Face Mask`, `Nasal Cannula`, `Room Air`) or no
device at all — i.e., clif-forge's generated `clif_truth.parquet` latent state
and its generated `respiratory_support` table diverge for a meaningful
fraction of hospitalizations in the sample dataset. **This is a finding to
raise with clif-forge's maintainer (JC), not something this bench papers
over.** It does not affect `T08`'s correctness — `T08`'s truth is computed
directly from `clif_respiratory_support.parquet`, independent of
`clif_truth.parquet` — but any future task built on `clif_truth.parquet`
`resp_flag` should account for this discrepancy.

## T02–T05, T09, T10: category-literal verification

For every task below, the category literal(s) hardcoded in `solution.py`/
`generate_truth.py` were checked against both (a) an actual `value_counts()`
over `bench/.data/subset/clif_*.parquet` and (b) the matching
`skills/clif-icu/schemas/*_schema.yaml` `permissible_values`, per the same
discipline as T08 above:

| Task | Column | Literal(s) | Present in subset? | In schema? |
|---|---|---|---|---|
| T02 | `respiratory_support.device_category` | `IMV` | yes (260 rows / 216 hospitalizations) | yes |
| T03 | `hospitalization.discharge_category` | `Expired` | yes (43 rows) | yes |
| T04 | `adt.location_category` | `icu` | yes (1150 rows) | yes |
| T05 | `medication_admin_continuous.med_category` | `norepinephrine` | yes (2509 rows, 160 hospitalizations) | yes |
| T09 | `patient.race_category`, `patient.sex_category` | all 7 race / 2 sex values in the subset | yes | yes |
| T10 | `labs.lab_category` | `potassium` | yes (7308 rows) | yes |

No literal needed correction. Note `T02`'s `n_imv_hospitalizations` (216)
is computed from the same `device_category == "IMV"` definition as `T08`'s
`n_imv_hospitalizations` and both independently land on **216** — a useful
cross-task sanity check that the literal and the counting logic are stable
across two separately-written solutions.

**T05 dose units**: `medication_admin_continuous.med_dose_unit` for
`norepinephrine` is **uniformly** `"mcg/kg/min"` across all 2509 rows in the
500-hospitalization subset (verified by `value_counts()` before writing
`truth_T05_norepi_dose`, which asserts this and raises if it ever stops
being true) — so no weight-based unit conversion is actually needed to get
a correct number here, though `solution.py` still calls clifpy's
`ClifOrchestrator.convert_dose_units_for_continuous_meds(preferred_units=
{"norepinephrine": "mcg/kg/min"})` per the brief, exercising the real
clifpy API. Note that call's `conversion_counts` reports `_convert_status`
`"cannot convert to a weighted unit if weight_kg is missing"` for **all**
2509 rows (this subset has **zero** `weight_kg` vitals rows for any of the
500 hospitalizations — verified), which looks alarming but is a red
herring here: clifpy's converter falls back to the original value when the
target unit already equals the source unit, and the fallback values are
verified numerically identical to the raw `med_dose` column (max diff
0.0). This absence of `weight_kg` matters much more for T06 below, where it
is not a no-op.

## T06: day-1 SOFA — independent-implementations pair, not clifpy-locked

The brief's original plan for T06 was to lock truth to `ClifOrchestrator.
compute_sofa_scores()`'s output at a pinned `clifpy` version (recording
`_clifpy_version` in `expected.json`). That plan was abandoned after
`compute_sofa_scores()` proved **not usable headlessly** against this
pinned subset once restricted to a day-1 (first 24h) cohort window — the
exact restriction T06 requires. Root-caused as follows:

1. `clifpy==0.5.0`'s `utils/sofa.py` uses DuckDB's `SELECT col: expr`
   colon-alias syntax, which raises `ParserException` under the
   `duckdb==0.10.2` that was resolvable in this environment. Fixed by
   installing `duckdb>=1.0` (see "Python version" note above) — this alone
   was not sufficient.
2. `compute_sofa()`'s cardiovascular-component query
   (`_agg_extremal_values_by_id`) selects a **fixed** column list including
   `dobutamine_mcg_kg_min`. That column only exists in the wide dataset if
   at least one `dobutamine` row survives unit conversion to `mcg/kg/min`.
   Conversion requires `weight_kg`, which — as noted under T05 above — is
   **entirely absent** from this subset's `vitals` table (0 of 500
   hospitalizations). Supplying a synthetic default weight unblocks
   conversion, but that's moot: every `dobutamine` administration in the
   500-hospitalization subset occurs **27–451 hours after admission**
   (verified directly against `clif_medication_admin_continuous.parquet`),
   i.e. *never* inside any hospitalization's day-1 window. So once
   `compute_sofa_scores()` is called with a day-1 `cohort_df`, the
   resulting windowed wide dataset has zero `dobutamine_*` rows for *any*
   hospitalization, the pivot never creates that column, and the
   fixed-column SQL raises `Binder Error: Column "dobutamine_mcg_kg_min"
   was selected but was not found in the FROM clause`. Confirmed this is
   specifically the day-1-window trigger by calling
   `compute_sofa_scores(id_name='hospitalization_id')` with **no**
   `cohort_df` (whole-encounter SOFA) — that succeeds, because dobutamine
   does appear somewhere across the full encounter for a few
   hospitalizations.

This is a genuine `clifpy` robustness bug (a fixed-column aggregation query
should tolerate an entirely-missing medication column, e.g. via
`COLUMNS(*)`-style dynamic selection or explicit fill, not crash), not a
data-quality issue this bench should paper over. Per the brief's documented
fallback ("if clifpy has NO usable SOFA computation, redefine T06's
solution+truth as an independent-implementations pair"), `T06_day1_sofa`
is implemented as **two independently-written pandas implementations of
the same fully-specified SOFA rubric** (rubric spelled out in
`prompt.md`, standard Vincent 1996 six-component SOFA, matching clifpy's
own `REQUIRED_SOFA_CATEGORIES_BY_TABLE` variable set for parity), not as a
clifpy-locked regression:

- `solution.py` computes each component per-hospitalization via a Python
  loop with scalar bin-lookup helper functions.
- `generate_truth.py`'s `truth_T06_day1_sofa()` computes the same rubric
  fully vectorized (one wide per-hospitalization table + `numpy.select`
  bin edges), with no per-hospitalization loop.

**Cardiovascular-component limitation (documented, not hidden)**: because
`weight_kg` is entirely absent from this subset, the cardiovascular
component only scores from `map` and `norepinephrine` (the one vasoactive
whose dose is already natively recorded in `mcg/kg/min` in this dataset —
see T05 above). `epinephrine`, `dopamine`, and `dobutamine` — all present
in the subset (204, 112, and 33 rows respectively) — are **excluded** from
the cardiovascular score, since scoring them would require fabricating a
weight. This under-scores hospitalizations on those other pressors
relative to a full clinical SOFA and is called out explicitly in
`prompt.md` so a scored agent isn't guessing at an undocumented rule.
Result: `n_scored=100`, `mean_day1_sofa=7.92` (range 2–16 across the
cohort) — plausible for an ICU-flavored synthetic cohort, not clustered at
an extreme.

## T07: hourly heart-rate binning — chosen semantic

`ClifOrchestrator.convert_wide_to_hourly()` (called on a `create_wide_dataset()`
wide frame) does **not** bin to wall-clock floor-hour; it produces hourly
windows anchored to each hospitalization's own admission time (window 0 =
`[admission_dttm, admission_dttm+1h)`, etc. — verified: window boundaries
land on e.g. `...:30:19`, matching a specific hospitalization's admission
timestamp, not `:00:00`). Separately, `create_wide_dataset()`'s pivoted
`event_time`/`heart_rate` columns were found to contain 138 rows with no
corresponding `(hospitalization_id, recorded_dttm)` pair in the raw
`vitals` parquet for the same cohort (2188 vs. 2050 heart-rate rows,
zero raw-only rows, 138 wide-only rows) — an unexplained discrepancy
introduced by `create_wide_dataset()`'s internal event-time assembly, not
reconcilable exactly against an independently-written pandas
implementation without reverse-engineering that internal logic.

Given the brief's explicit instruction to "reconcile deliberately and
document the chosen semantic" when clifpy's binning differs from a plain
pandas approach: `T07`'s chosen semantic is (1) **admission-anchored**
hourly windows (not wall-clock floor), spelled out exactly in `prompt.md`,
and (2) data assembly via `ClifOrchestrator.load_table()` (clifpy's
table-level loader, schema/config-validated — verified byte-identical to a
raw `pd.read_parquet` read for this table/filter: 2050 rows, max value
diff 0.0) rather than `create_wide_dataset()`'s pivot, specifically to
avoid the unreconciled 138-row discrepancy above. `solution.py` uses
`co.load_table('vitals', filters=...)` (still a real clifpy API call) then
applies the documented admission-anchored binning in pandas;
`truth_T07_hourly_wide()` reads the same `vitals`/`hospitalization`
parquet directly with no clifpy dependency, applying the identical binning
formula independently. Both land on `n_rows=2050`,
`mean_heart_rate=88.57`.

**`create_wide_dataset()`/`load_table()` API note**: `hospitalization_ids`
filters passed to both functions must be **strings**, even though the
underlying parquet's `hospitalization_id` column is `int64` — passing
`int`s silently filters every base table to 0 rows (no error), which was
initially mistaken for missing data before being traced to the type
mismatch.

## Config key name

`solve()` reads `data_directory` out of the config JSON. Verified against the
config clifpy's `create_example_config` actually writes
(`clifpy==0.5.0`, JSON format): the key is `data_directory` — matches the
brief; no solution changes were needed. Note `create_example_config` writes
whatever path string it's given verbatim: `setup_bench_data.sh` passes an
**absolute** path (`Path("./subset").resolve()`), not `pin.json`'s or the
brief's original relative `"./subset"` — a relative path only resolves
correctly when the reading process's cwd happens to be `bench/.data/`, which
is not true when pytest is invoked from `bench/` (the documented workflow).
This was caught by running the full pipeline end-to-end (`FileNotFoundError`
on the first `pytest` run) and fixed at the source (`setup_bench_data.sh`)
rather than worked around in `solution.py`/`harness.py`.

## Adding a task (T02–T10, or a new site task)

1. Copy an existing task directory, e.g. `bench/tasks/T01_crrt_cohort/` →
   `bench/tasks/T02_<slug>/`.
2. Write `prompt.md` (the question the agent sees — no scoring hints) and
   `solution.py` (`solve(config_path: str) -> dict`, aggregates only).
3. Add a `truth_T02_<slug>()` function to `generate_truth.py`, written
   **independently** of `solution.py` (different implementation approach
   where feasible — e.g. `groupby` vs. set arithmetic) so a shared bug in one
   doesn't silently confirm the other.
4. Regenerate: `python3 bench/generate_truth.py T02` (or omit the task ID to
   regenerate everything), then `cd bench && python3 -m pytest test_bench.py -v`.
5. If your reference solution and the independently-written truth disagree,
   debug to the root cause before committing — a mismatch between two
   independent implementations means one of them has a real bug.
