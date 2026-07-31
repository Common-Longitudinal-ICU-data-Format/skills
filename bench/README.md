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

Expected result: `T01_crrt_cohort` and `T08_category_trap` both `PASSED`.
`bench/setup_bench_data.sh` requires `pandas`, `pyarrow`, and `clifpy`
(`python3 -m pip install --user pandas pyarrow clifpy` if missing) plus network
access to `github.com` to clone clif-forge.

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
task is interesting — an agent under test should not get a hint. The trap:
this dataset is CLIF **2.1**, whose `respiratory_support.device_category`
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
