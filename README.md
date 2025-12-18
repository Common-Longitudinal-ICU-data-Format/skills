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
| **clif-icu** | Analyzes ICU clinical data using CLIF format and clifpy. Loads tables, computes SOFA/CCI/Elixhauser scores, creates wide datasets. |

---

## Repository Structure

```
clif-skills/
├── .claude-plugin/
│   └── marketplace.json        # Plugin registration
├── skills/
│   └── clif-icu/               # CLIF ICU skill
│       ├── SKILL.md            # Skill definition
│       ├── reference/          # Documentation
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
