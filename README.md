# CLIF Skills Plugin

Claude Code plugin providing skills for working with **CLIF** (Common Longitudinal ICU data Format) and the **clifpy** Python library.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## Installation

### 1. Install clifpy

```bash
pip install clifpy
```

### 2. Install Skill

#### Via Plugin Marketplace

```bash
/plugin marketplace add Common-Longitudinal-ICU-data-Format/skills
/plugin install clif-icu@clif-skills
```

#### Manual

Copy `skills/clif-icu` to:
- Personal: `~/.claude/skills/clif-icu/`
- Project: `.claude/skills/clif-icu/`

---

## Available Skills

| Skill | Description |
|-------|-------------|
| **clif-icu** | Analyzes ICU clinical data using CLIF format and clifpy. Loads tables, computes SOFA/CCI/Elixhauser scores, creates wide datasets. Self-enforces a **PHI-safe agentic workflow** and is **CLIF version-aware** (2.1 stable / 3.0 multimodal). |

---

## Agents

Three review agents ship with the plugin (`agents/`), so every site gets the same
discipline without writing its own prompts. All three are read-only
(`Read, Grep, Glob, Bash`) and report evidence-backed findings — the human makes
the call.

| Agent | Use it when |
|-------|-------------|
| **clif-buddy-tester** | Buddy testing a CLIF study kit before it goes to the consortium — does it run at your site, produce every promised poolable artifact, and stay PHI-safe? |
| **clif-phi-auditor** | Before sharing, pushing, or distributing any CLIF artifact — scans repos, results, figures, logs, and output bundles for PHI leakage and small-cell risk. |
| **clif-code-reviewer** | Reviewing CLIF analysis code (Python/clifpy, R, SQL, notebooks) before it runs on real data — catches the CLIF-specific footguns that produce plausible-but-wrong multi-site results. |

---

## PHI-Safe Agentic Development

When an AI agent helps you write or debug CLIF code, **the agent must never receive
PHI/RHI (real patient data)** — an agent session captures stdout *and* uncaught
tracebacks. The skill self-enforces this two-phase workflow:

1. **Develop with the agent against non-PHI data only** — synthetic/demo CLIF data.
   Run `skills/clif-icu/scripts/setup_dev_data.sh --source clif-forge-sample ./dev_data` for the fastest path to a non-PHI sandbox, or see [`reference/synthetic-datasets.md`](skills/clif-icu/reference/synthetic-datasets.md) for other options.
2. **Run on real PHI yourself**, in your own secure/HIPAA environment, with the agent
   absent. Sanitize before pasting anything back — never raw tracebacks, row previews,
   IDs, dates, note text, or small-cell counts.

The example scripts default to the non-PHI demo config and refuse to run against a
non-demo config unless you explicitly confirm no agent is watching
(`CLIF_ALLOW_REAL_DATA=1`); counts are small-cell suppressed as defense in depth.

This is risk-reduction guidance, **not legal/compliance advice** — clear any real-data
workflow with your IRB/privacy/security office. Full guide:
[`reference/phi-safe-development.md`](skills/clif-icu/reference/phi-safe-development.md).

### PHI hooks (mechanical enforcement)

The plugin ships two Claude Code hooks (`hooks/hooks.json`) that turn the guidance
above into enforcement. Details and known limitations: [`hooks/README.md`](hooks/README.md).

- **`hooks/phi_guard.py`** — `PreToolUse` on `Read|Glob|Grep|Bash|Edit|Write|NotebookEdit`.
  Blocks (exit 2) any tool call whose path argument resolves under a configured
  real-data directory, or whose Bash command text contains one of those paths.
- **`hooks/phi_scan.py`** — `PostToolUse` on `Read|Bash`. Scans tool output
  (recursing through nested payloads) for MRN-, SSN-, and birth-date-shaped
  patterns and warns the agent to sanitize. **Advisory, never blocks** — synthetic
  data trips it by design.

**Configure:** one absolute directory path per line, `#` comments allowed. The guard
reads the union of all of these that exist:

1. `$CLIF_PHI_PATHS_FILE`
2. `./.clif-phi-paths` (current working directory)
3. `~/.clif/phi-paths`

```
# .clif-phi-paths
/data/<site>/real_data
/scratch/cohort_exports
```

**Off-switches** (know them, so you know when you are unprotected):

- The guard is **inactive until configured** — with none of the three sources
  present, it allows everything. Deleting `.clif-phi-paths` silently disables it.
- `CLIF_PHI_SCAN=off` disables the advisory output scanner.

**Limits:** Bash matching is substring-only (relative paths, shell variables, and
globs are not caught); it may over-block on case-sensitive filesystems; it works in
Claude Code only; and it is risk reduction, **not a sandbox and not compliance**.
See "Known Limitations" in [`hooks/README.md`](hooks/README.md).

---

## clif-bench

`bench/` is a golden-task benchmark for the skill: **10 tasks** (`T01`–`T10`) run
against pinned, synthetic (non-PHI) CLIF data, currently **10/10 passing**. Each
task's ground truth is *generated* (never hand-edited) by an implementation written
independently of the reference solution, so a shared bug in one cannot silently
confirm the other. Data is pinned by SHA and deterministically re-derivable.

```bash
bash bench/setup_bench_data.sh          # pinned data into bench/.data (git-ignored)
cd bench && python3 -m pytest test_bench.py -v
```

Requires **Python 3.10+** plus `pandas`, `pyarrow`, `clifpy`, `pyyaml`, and
`duckdb>=1.0`, and network access to `github.com`. To score an *agent* rather than
the reference solutions — give it only `prompt.md`, have it write its own
`solve(config_path) -> dict`, report N passed / N total — follow "How to score an
agent" in [`bench/README.md`](bench/README.md).

---

## CLIF version awareness (2.1 vs 3.0)

The skill targets **CLIF 2.1** (current stable) by default and is aware of **CLIF 3.0**
(the July 2026 multimodal release, which changes category conventions and adds imaging +
clinical-notes tables). Declare your target with `CLIF_SCHEMA_VERSION=2.1|3.0`; the
scripts echo and validate the value but do **not** auto-crosswalk — on the `3.0` path
they warn that 2.1-convention filters may silently match zero rows. Migration 2.1 → 3.0
is a deliberate, audited step (clifpy crosswalk). See the "CLIF version: 2.1 vs 3.0"
section of the PHI-safe guide.

---

## Repository Structure

```
clif-skills/
├── .claude-plugin/
│   └── marketplace.json        # Plugin registration (skills + agents + hooks)
├── skills/
│   └── clif-icu/               # CLIF ICU skill
│       ├── SKILL.md            # Skill definition
│       ├── reference/          # Documentation (incl. phi-safe-development.md,
│       │                       #   synthetic-datasets.md)
│       ├── scripts/            # Runnable examples + dev-sandbox bootstrapper
│       │   ├── setup_dev_data.sh                # one-command non-PHI sandbox
│       │   ├── cohort_identification_example.py # CRRT cohort walkthrough
│       │   ├── sofa_score_calculation.py        # SOFA scoring walkthrough
│       │   └── tests/                           # network-free failure-path tests
│       ├── mCIDE/              # Standardized vocabulary
│       └── schemas/            # YAML schema definitions
├── agents/                     # Consortium review agents (ship with the plugin)
│   ├── clif-buddy-tester.md    # Study-kit buddy test / QA
│   ├── clif-phi-auditor.md     # Pre-share PHI + small-cell audit
│   └── clif-code-reviewer.md   # CLIF correctness review
├── hooks/                      # Claude Code PHI hooks
│   ├── hooks.json              # PreToolUse / PostToolUse registration
│   ├── phi_guard.py            # Blocks reads of configured real-data paths
│   ├── phi_scan.py             # Advisory PHI scan of tool output
│   └── tests/                  # Hook test suite
├── bench/                      # clif-bench: 10 golden tasks on pinned synthetic data
│   ├── tasks/                  # T01–T10 (prompt.md, solution.py, expected.json)
│   ├── generate_truth.py       # Independent ground-truth generator
│   ├── harness.py              # Comparison harness
│   ├── setup_bench_data.sh     # Stands up pinned data in bench/.data (git-ignored)
│   └── pin.json                # Data-source pin (repo + SHA)
├── docs/
│   ├── memo/                   # Consortium strategy memos
│   └── plans/                  # Design + implementation plans
├── README.md                   # This file
└── LICENSE
```

---

## About CLIF

**CLIF** (Common Longitudinal ICU data Format) is a standardized format for ICU clinical data enabling multi-center research and collaboration.

- Official Website: [clif-icu.com](https://clif-icu.com/)
- Python Library: [clifpy on PyPI](https://pypi.org/project/clifpy/)

---

## License

Apache 2.0
