# Sprint 1: The Trust Layer — Design

**Date:** 2026-07-31
**Status:** Draft — pending review
**Goal:** Attack the three observed frictions blocking consortium AI adoption — PHI anxiety,
output correctness, fragmented tooling — with mechanical (not prose) solutions, all
distributable as files/repos (no central infrastructure).

## Context

- Audience: clinician-researchers (mixed tools), site ETL engineers, data scientists with
  Claude Code. Portability matters; Claude Code plugin is the deepest integration.
- Constraint: files-only distribution. Sites run everything inside their own firewalls.
- Assets nobody is using yet: two synthetic CLIF generators —
  `synthetic_clif` (Aartik: 28 tables, hand-specified priors, pre-generated 10k release) and
  `clif-forge` (JC: empirically calibrated, committed in-repo samples, reproducible recipes,
  built for agent development / CI fixtures).
- `clifpy` provides validation, DQA, and clinical calculations — the ground-truth engine.

## Deliverables (all in this skills repo)

### 1. Unified synthetic sandbox (small)

`skills/clif-icu/scripts/setup_dev_data.sh` gains a `--source` flag:

- `synthetic-clif` — current behavior (clone + generate small cohort)
- `clif-forge-sample` — clone clif-forge, use committed sample dataset (fastest path; no
  generation step)
- `clif-forge-generate` — generate a custom cohort from a recipe

Plus a short reference page: *which synthetic dataset for which job* (priors vs. empirical
calibration, size, redistribution, reproducibility).

Ask each PI to cut a version tag so downstream consumers (sandbox, bench) can pin.

### 2. PHI guardrail hooks (medium)

Shipped in the plugin's `hooks/` directory:

- **PreToolUse hook**: blocks Read/Bash/Glob/Grep access to real-data paths the site lists in
  a local config file (e.g. `~/.clif/phi-paths.txt` or project-level `.clif-phi-paths`).
  Fail-closed messaging tells the user *why* and how to configure.
- **Output scan hook** (PostToolUse or Stop): flags PHI-shaped patterns in tool output —
  MRN-like identifiers, DOB-like dates, small-cell counts, `patient_id`/`hospitalization_id`
  value dumps.

Design principles: site-configurable, fail-closed on PHI paths, advisory (warn) on pattern
scans to limit false-positive friction. Turns "please don't" prose into "the tool cannot" —
the key sentence for IRB/privacy conversations.

Honest limitation, documented: hooks exist only in Claude Code. The portability matrix
(phase B) states which guardrails degrade in other tools.

### 3. clif-bench v0 (the meaty one)

`bench/` in this repo. ~10–15 golden tasks against a **pinned** synthetic dataset
(clif-forge sample, by version tag). Each task:

- a natural-language prompt (what a researcher would actually ask), e.g. "identify the CRRT
  cohort", "compute day-1 SOFA", "hourly wide dataset for vitals", a unit-conversion task,
  a 2.1-vs-3.0 category trap
- ground truth precomputed with clifpy, committed as small artifacts
- a `pytest` runner that checks agent-produced code output against ground truth

Triple duty:

1. CI for the skill — catches skill/model regressions on every edit
2. Citable correctness numbers for the strategy memo (skill-assisted vs. raw prompting)
3. A template sites can extend with their own tasks

Spin out to its own repo only if sites start extending it.

### 4. Consortium agents (`agents/` in the plugin)

- **clif-buddy-tester** — migrate from author's personal `~/.claude/agents/` into the plugin
  (QA a federated study kit before distribution; evidence-backed findings; human keeps
  judgment calls)
- **clif-phi-auditor** — new: pre-flight scan of a repo/results before sharing or pushing —
  PHI patterns, small cells, dates, ID columns, hardcoded site paths
- **clif-code-reviewer** — new: reviews CLIF analysis code for the known footgun list —
  wrong category values (2.1 vs 3.0 conventions), timezone bugs, unit errors,
  patient-vs-hospitalization join mistakes, missing small-cell suppression

Backlog (not sprint 1): clif-etl-validator (clifpy DQA triage), clif-migration-assistant
(audited 2.1→3.0 crosswalk).

### 5. Strategy memo (drafted after 1–4 exist)

Drafted in `docs/` here; ships to consortium channels. Written as a short leadership memo
with a technical appendix. Contents: landscape survey (Agent Skills open standard, MCP,
hooks, evals, synthetic data, BAA channel matrix), the sprint-1 artifacts as evidence
(hooks = PHI answer, bench numbers = correctness answer, sandbox = onboarding answer),
and the A→B→C roadmap as the consortium's recommended path.

## Repo boundaries

| Component | Lives in | Relationship |
|---|---|---|
| Skill, hooks, agents, sandbox script, bench, memo draft | **this skills repo** | one `/plugin install` delivers everything |
| synthetic_clif, clif-forge | their own repos | consumed by clone + version pin; small ask: version tags |
| clifpy | its own repo | ground-truth engine; untouched unless bench finds bugs (upstream them) |
| Project template repo | new repo | **phase B, not sprint 1** |

## Explicitly out of scope (phase B/C)

MCP server, R support, skill splitting by persona, project template repo, portability
matrix docs. Sequencing: trust (A) → portability (B) → ecosystem (C).

## Success criteria

- A new user reaches a working non-PHI sandbox in one command, two sources available
- Hooks demonstrably block a read of a configured PHI path in Claude Code
- `pytest bench/` runs green locally against pinned synthetic data; at least 10 tasks
- The three agents install with the plugin and are invocable at any site
- Memo draft exists with real artifacts to cite
