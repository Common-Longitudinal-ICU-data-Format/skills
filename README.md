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
│   └── marketplace.json        # Plugin registration
├── skills/
│   └── clif-icu/               # CLIF ICU skill
│       ├── SKILL.md            # Skill definition
│       ├── reference/          # Documentation (incl. phi-safe-development.md)
│       ├── scripts/            # Runnable examples + dev-sandbox bootstrapper
│       │   ├── setup_dev_data.sh                # one-command non-PHI sandbox
│       │   ├── cohort_identification_example.py # CRRT cohort walkthrough
│       │   ├── sofa_score_calculation.py        # SOFA scoring walkthrough
│       │   └── tests/                           # network-free failure-path tests
│       ├── mCIDE/              # Standardized vocabulary
│       └── schemas/            # YAML schema definitions
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
