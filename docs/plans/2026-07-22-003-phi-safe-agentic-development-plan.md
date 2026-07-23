---
title: Add PHI-safe agentic-development best practices to the clif-icu skill
date: 2026-07-22
type: feature
origin: CLIF community discussion on PHI-safe agent workflows (synthetic_clif plug)
status: shipped
---

# PHI-safe agentic development for clif-icu

## Goal Capsule

Codify a workflow where an AI agent helping write/debug CLIF code **never receives
PHI/RHI**: the agent develops against non-PHI synthetic/demo data, the researcher
runs on real data themselves in a secure environment, and any real-data error is
sanitized (and ideally passed only through a BAA-covered channel) before it reaches
the agent. Make the skill self-enforce this and give users a one-command non-PHI
sandbox.

## Findings (verified 2026-07-22)

| Area | Status | Action |
|------|--------|--------|
| Existing skill privacy/PHI content | None | Net-new section + reference doc |
| clifpy bundled demo dataset | Does not exist | Point at external non-PHI data via `data_directory`/config |
| `synthetic_clif` | MIT, no PHI, CLIF **2.1.0**, ~10k hosp / ~33M rows / 28 tables | Primary sandbox option; helper script |
| MIMIC-IV-Ext-CLIF | PhysioNet credentialed + DUA-gated, 14 tables, real-derived, small demo N | Co-equal option; agent must not fetch/embed |
| Anthropic BAA (as of 2026-07) | API + Enterprise covered; Claude Code only w/ ZDR; not Bedrock/Vertex/Console | Document with links + "verify / not legal advice" |
| Example scripts config keys | Use `tables_path`/`file_type` (YAML-variant), != `create_example_config`'s `data_directory`/`filetype` | Documented as known wrinkle; scripts not rewritten |
| synthetic_clif 2.1.0 vs skill 2.1.1 | Patch delta; `*_category` lists unchanged; clifpy 0.5.0 `2.1` schemas validate both | Documented as dev-safe with two caveats |

## Changes

- **U1** — `SKILL.md`: new `## Critical: PHI-Safe Agentic Development` section
  (before `When to Use This Skill`) — core rule, 4-step workflow, two co-equal
  non-PHI datasets, "never paste PHI" rule, link to the reference doc.
- **U2** — new `reference/phi-safe-development.md`: threat model; non-PHI setup
  (synthetic_clif + MIMIC + `create_example_config` snippet); running on real PHI;
  sanitization guidance; HIPAA-channel guidance w/ links + non-advice disclaimer;
  checklist; 2.1.0-vs-2.1.1 version note; related-docs table.
- **U3** — new `scripts/setup_dev_data.sh`: clone/install synthetic_clif → generate
  a small non-PHI cohort → write `clif_demo_config.json`; defensive generation
  detection with instructions fallback; PHI-safe reminders.
- **U4** — `scripts/cohort_identification_example.py` and `sofa_score_calculation.py`:
  PHI-SAFE banner comment (no functional change).
- **U5** — `SKILL.md` cross-links: Quick Start (both loaders), Example Scripts entry
  for `setup_dev_data.sh`, Reference Files table row, Requirements bullet.
- **U6** — `reference/clifpy_utils/configuration.md`: back-link to the new doc.
- **U7** — `.claude-plugin/marketplace.json`: version `1.2.3` → `1.3.0`.
  **Delivery correction (2026-07-23):** this `1.2.3 → 1.3.0` assumed sitting on
  PR #2's unmerged `1.2.3`. PR #2 never merged, so the actual base was `1.1.0`
  and this work shipped as **`1.1.0 → 1.2.0`** (current `marketplace.json` value).
  The version reconciles with PR #2 at its merge time. See plan `004`'s "Delivery
  update" for the full reconciliation.
- **U8** — two-phase deployment toggle: develop on a consumer **Max/Pro plan + fake
  data** (fine — no PHI), then **toggle Claude to a BAA-covered channel** for real
  data — first-party API/Enterprise (Claude Code w/ ZDR) *or* Claude on a
  HIPAA-eligible cloud (Bedrock/Vertex under the cloud provider's BAA). Added an
  explicit **confirmation/verification gate (Q1–Q4)**: verify the active credential
  is the covered API key (via `/status` + env vars), **not** the Max plan, before
  any PHI. Documented in SKILL.md §PHI-safe and reference §4 + checklist Phase B.

## Guardrails baked into content

- No HIPAA over-claiming; risk-reduction framing + "verify with IRB/privacy office".
- synthetic_clif MIT (freely shareable); MIMIC credentialed/DUA-gated, no scripted
  download; agent references the researcher's own copy only.
- BAA/ZDR/Bedrock-Vertex facts timestamped, link-first, "re-verify".
- 2.1.0-vs-2.1.1 delta and the example-script config-key mismatch documented, not hidden.

## Out of scope

- Rewriting the example scripts' `tables_path`/`file_type` config loading (future work).
- Any CLIF v3.0 content.
