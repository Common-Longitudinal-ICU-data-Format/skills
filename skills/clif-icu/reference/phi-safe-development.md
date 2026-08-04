# PHI-Safe Agentic Development with CLIF

How to use an AI agent (Claude, Claude Code, Claude Enterprise, etc.) to write and
debug CLIF code **without ever exposing PHI/RHI** — protected / real patient health
information — to the agent.

**People are already using AI agents to write and debug CLIF code.** This is a good
thing — done correctly, the agent never touches real patient data. This document is
the *correct* way to do it.

## The rule is universal for CLIF agentic coding

This is not advice specific to clif-icu *analysis*. It is a **universal principle**
for **any agent writing or debugging any CLIF code** — clifpy pipelines, R-package
work, ETL into CLIF, ad-hoc scripts, notebooks, anything. The `clif-icu` skill
*states and self-enforces* this rule within its own context, but the principle
applies **everywhere you point an agent at CLIF work**, regardless of which tool,
language, or repository you are in.

## The canonical workflow (follow these steps)

1. **Develop against non-PHI data.** The agent writes and debugs your code against
   **synthetic or demo** CLIF data only. If your organization has **Claude
   Enterprise**, use it here too (one less channel to switch later). But **any**
   channel — a consumer **Max/Pro** plan or the **first-party API** — is fine for
   this step, *because the agent only ever sees synthetic data.* A BAA-covered
   channel becomes **required only at step 2/3, when real PHI is involved.**
2. **You run the code on real PHI/RHI yourself** — manually, inside your own
   secure/HIPAA environment. **The agent is not present for this step.**
3. **To debug real-data errors, sanitize first (see §3).** If you have a
   **HIPAA-compliant chat / BAA-covered channel**, move the debugging there (see
   §4). Otherwise, sanitize and stay on non-PHI data.

## Threat model / core principle

An AI agent is an **untrusted party for PHI**: anything you paste into the
conversation may leave your controlled environment. So the workflow separates two
roles that most people accidentally merge:

- **Code authoring** — done *with* the agent, against **non-PHI** synthetic or demo
  data only.
- **Code execution on real data** — done *by the researcher*, alone, inside their
  own secure/HIPAA environment. The agent is never present for this step.

**The agent writes the code; the human runs it on PHI.** This holds regardless of
clifpy version, dataset, or institution.

> **Unconditional guard — never relaxed:** *Never paste raw PHI/RHI or a raw
> traceback into ANY agent conversation — not even a BAA-covered one.* A covered
> channel reduces *channel* risk; it is **not** a license to paste raw patient data.
> The default is always sanitize-first (§3). "Move debugging to a HIPAA-compliant
> chat" (§4) changes *where* the conversation happens, not *whether* you minimize.

---

## Mechanical enforcement

This document is guidance for a human; the plugin also ships mechanical
enforcement so the workflow doesn't rely on discipline alone. Two Claude Code
hooks (`hooks/hooks.json`) run automatically in any Claude Code session with
this plugin installed: a `PreToolUse` guard (`hooks/phi_guard.py`) that blocks
tool calls touching a configured real-data directory, and a `PostToolUse`
scanner (`hooks/phi_scan.py`) that advisorily flags PHI-shaped patterns in
tool output. Configuration (listing your site's real-data directories) and
known limitations (Bash matching is substring-only, Claude Code only, inactive
until configured, and more) are documented in
[`hooks/README.md`](../../../hooks/README.md) — read it before relying on the
guard.

---

## 1. Set up a non-PHI dev environment

You point clifpy at data you supply. (No *documented* bundled demo loader was found
in the clifpy README/published docs — checked 2026-07-22, v0.5.0; if your installed
version ships one, use it.) For agent-assisted work, that data must contain no PHI.
Options, pick based on your constraints:

| Option | License / access | Data | Best when |
|--------|------------------|------|-----------|
| **synthetic_clif** | MIT, no credentialing | Fully synthetic CLIF **2.1.0**; pre-generated set ≈ 10k hospitalizations / ~33M rows / all 28 tables (`clif_<table>.parquet` or CSV) | You want a large-N sandbox with zero data-use paperwork, safe to share freely |
| **clif-forge** | Free, openly redistributable — no release tags upstream yet, pinned by commit SHA | Empirically calibrated to aggregate CLIF statistics (not just hand-specified priors); committed in-repo sample dataset (`sample_dataset/`), CLIF 2.1, ~20 tables | You want a fast, redistributable non-PHI sandbox with statistically realistic distributions, clone-and-go (no generation step) |
| **MIMIC-IV Clinical Database Demo** | Open, **ODbL** (attribution + share-alike) | **Raw MIMIC-IV, NOT CLIF-formatted** — 100 patients, de-identified, excludes free-text notes; needs a CLIF-MIMIC ETL to become CLIF | You want an open, real-derived structure and are willing to run the ETL; no credentialing |
| **MIMIC-IV-Ext-CLIF** | PhysioNet **credentialed + DUA-gated** | Real-derived (de-identified), already CLIF-formatted, 14 tables | You specifically need real-derived CLIF structure; note the demo N is small enough to distort analyses |

> Full option-by-option comparison, including which to pick for agent-assisted
> development vs. statistical realism: [synthetic-datasets.md](synthetic-datasets.md).

> **synthetic_clif** — https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif
> **MIMIC-IV Clinical Database Demo** — https://physionet.org/content/mimic-iv-demo/ (open, ODbL)
> **MIMIC-IV-Ext-CLIF** — https://physionet.org/content/mimic-iv-ext-clif/1.1.0/ (credentialed)

**The open demo and the credentialed dataset are different things — keep them
separate.** The **open MIMIC-IV Clinical Database Demo** (ODbL) is freely
downloadable, but it is *raw MIMIC*, not CLIF, and carries an attribution/share-alike
license obligation.

**MIMIC-IV-Ext-CLIF is credentialed:** the agent must **not** fetch, download, or
embed it. Only the researcher, under their own PhysioNet credentials and DUA, may
obtain it, and it stays in their environment. Do not script an automated download of
the credentialed dataset. `synthetic_clif`, being MIT and PHI-free, has no such
restriction.

### synthetic_clif quick setup

```bash
git clone https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif
cd synthetic_clif
# Pin to a tagged release so CLI behavior and data provenance are reproducible —
# an unpinned branch can change silently between runs. (v0.7.0 == main HEAD as of
# 2026-07-23; list current tags with `git ls-remote --tags <repo-url>`.)
git checkout v0.7.0
python3 -m pip install -e .
# Generate a SMALL cohort for fast agent-loop iteration into ./dev_data.
# (CLI verified against docs 2026-07-22; run `python3 -m synthetic_clif --help`
#  as ground truth if flags have changed.)
python3 -m synthetic_clif --hospitalizations 100 --output ./dev_data \
        --format parquet --seed 42
```

The one-command helper [`scripts/setup_dev_data.sh`](../scripts/setup_dev_data.sh)
automates the clone/install/generate, pins the resolved ref, and writes a demo
config. It supports three sources via `--source {synthetic-clif|clif-forge-sample|
clif-forge-generate}` (default `synthetic-clif`): `synthetic-clif` clones and
generates with `synthetic_clif` (override the pin with `CLIF_SYNTHETIC_REF`);
`clif-forge-sample` copies clif-forge's committed sample dataset as-is, no
generation step; `clif-forge-generate` clones and generates a custom cohort with
the `clif-forge` CLI (override the pin with `CLIF_FORGE_REF`). All three record
the resolved commit SHA for provenance. See
[synthetic-datasets.md](synthetic-datasets.md) for which to pick.

### Point clifpy at the non-PHI data

Use the canonical config keys (`data_directory`, `filetype`, `timezone`,
`output_directory`) — see [clifpy_utils/configuration.md](clifpy_utils/configuration.md):

```python
from clifpy.utils.config import create_example_config

create_example_config(
    data_directory="./dev_data",          # the synthetic_clif output folder
    filetype="parquet",
    timezone="US/Central",
    output_directory="./output",
    config_path="./clif_demo_config.json",
)
```

```python
from clifpy import ClifOrchestrator

co = ClifOrchestrator(config_path="./clif_demo_config.json")
# or, with no args, clifpy auto-detects config.json / config.yaml in the cwd.
```

> **Config keys — both variants work.** `create_example_config` writes
> `data_directory` / `filetype`; some hand-written YAML configs use the variant
> names `tables_path` / `file_type`. `ClifOrchestrator(config_path=...)` parses the
> config natively, so `sofa_score_calculation.py` (which hands the path straight to
> the orchestrator) accepts either. `cohort_identification_example.py` reads the
> config dict itself and now accepts **both** key sets via a small loader shim, and
> defaults to this demo config — so a `create_example_config` file is drop-in for
> both scripts.

---

## 2. Run on real PHI locally (researcher only)

Inside your own secure/HIPAA environment, swap `data_directory` / `config_path` to
your **real-data** config and run the agent-authored code yourself. The agent is
not in the loop here. No real paths, logs, dataframes, or tracebacks return to the
conversation unsanitized (see next section).

---

## 3. Sanitize errors/outputs before sharing with an agent

Sometimes a bug only reproduces on real data. Before showing an agent **anything**
derived from PHI, sanitize it.

**What counts as PHI in CLIF/ICU data:**
- Patient / MRN identifiers; `patient_id` and `hospitalization_id` values.
- **All dates and timestamps** — admission, discharge, event, lab/vital times.
- Free-text fields — clinical `note` text, microbiology organism free text,
  assessment comments.
- Geographic / site / hospital identifiers.
- **Small-cell counts** — cohort or subgroup sizes below your site's threshold
  (commonly < 11) can re-identify patients even without direct identifiers.

**How to sanitize:**
- Share only the **exception type + the failing line**, not the full traceback with
  data values.
- Replace real IDs with **synthetic placeholders** (`H001`, `P001`).
- Redact or shift dates; never paste real timestamps.
- **Never** paste `.head()` / `.sample()` / `value_counts()` / dataframe previews of
  real rows.
- Suppress or aggregate small cells before reporting counts.
- **Structured outputs / JSON schema:** never place PHI in a schema's `names`,
  `enum`, `const`, or `pattern` values. Unlike table *data* the model merely reads,
  these schema fields are transmitted verbatim as part of the request — a patient ID
  baked into an `enum` is exposed just as surely as one pasted into the chat.

**Best of all:** reproduce the error on your **synthetic_clif** sandbox and share
*that* traceback — it contains no PHI by construction.

---

## 4. The two-phase deployment toggle (dev plan → covered channel)

The safest posture is still: the agent never sees PHI at all (develop on synthetic
data in Phase A; run real data in Phase B with no agent present). But if you *do*
need Claude in the loop on real data, use this explicit two-phase toggle.

**Phase A — Development (NO PHI).** Any Claude works here — including a **consumer
Max / Pro subscription** — *because it only ever sees synthetic/demo data.* The
plan's data-handling terms are irrelevant when no PHI is present. Build and debug
your code here.

**Phase B — Real data (PHI).** Before real data touches Claude, **toggle the
deployment to a BAA-covered channel.** Never run PHI on a Max/Pro consumer
subscription. Covered options:

| Route | Whose BAA | Notes |
|-------|-----------|-------|
| First-party **Claude API** on a HIPAA-ready org | **Anthropic** BAA | **Does *not* require ZDR.** HIPAA-readiness and Zero Data Retention are configured on **separate orgs** — they are distinct settings, not the same toggle |
| **Claude Code** | **Anthropic** BAA | Covered **only with Zero Data Retention (ZDR) enabled**, on a qualified first-party API org **or** Claude Enterprise |
| **Claude Enterprise** | **Anthropic** BAA | Covered enterprise deployment |
| Claude on your org's **HIPAA-eligible cloud** — **Amazon Bedrock** or **Google Vertex AI** | **the cloud provider's** BAA (AWS / GCP) | There the cloud provider is your business associate; Anthropic's BAA does not apply. Verify Claude availability + HIPAA eligibility for your specific platform |

**Gotcha — Covered Models:** certain models (e.g. **Fable 5**, **Mythos 5**)
**cannot** be BAA-covered when used through Claude Code / Cowork, even on an
otherwise-covered org. Confirm the specific model is in scope.

**Never covered:** consumer **Free / Pro / Max / Team**, the **Console / Workbench**,
**Cowork**, **beta features**, and **web search**.

> **⚠ Confirm current status for YOUR org before any PHI.** The facts above *relax*
> a prior constraint (the API no longer needs ZDR) — but BAA scope, ZDR
> configuration, and covered-model eligibility are **perishable and org-specific**.
> A stale snapshot must never be the basis for sending PHI. Re-verify your own org's
> current coverage against the official docs below *before* real data flows. This
> table documents the general shape; it is **not** a standing guarantee for your
> account.

### Confirmation & verification gate — run BEFORE any PHI

Answer **YES to every question** before pointing Claude at real data. If any answer
is no or unknown, stop.

- **Q1 — Which credential/endpoint is active right now?** Confirm it is the
  **covered API key / cloud endpoint**, *not* the Max/Pro subscription login.
  - In Claude Code: run **`/status`** to see the active auth method and account;
    check environment — `ANTHROPIC_API_KEY` set (org key, not personal),
    `CLAUDE_CODE_USE_BEDROCK=1` for Bedrock, or `CLAUDE_CODE_USE_VERTEX=1` for
    Vertex; confirm you are **not** signed in via a consumer subscription.
    *(Verify exact commands/flags against your Claude Code version's docs.)*
- **Q2 — Is that deployment covered by a signed BAA?** Anthropic BAA for
  first-party API/Enterprise; AWS/GCP BAA for Bedrock/Vertex.
- **Q3 — If using Claude Code, is Zero Data Retention enabled?** (ZDR is required
  for **Claude Code**; the first-party **API** on a HIPAA-ready org does **not**
  require it — they are separate orgs.)
- **Q4 — Is the specific model a Covered Model for your route** (not a Fable/Mythos
  model excluded under Claude Code / Cowork)?
- **Q5 — Has your IRB / privacy / security office approved this deployment for
  PHI?**

Only when every question is YES may real data flow — **and even then, sanitize
first (§3): a covered channel is not permission to paste raw PHI or raw tracebacks.**

**As of 2026-07 (verify before relying — this changes over time)** — source of
truth, check the current version, don't trust this snapshot:
- https://support.claude.com/en/articles/8114513 (BAA for commercial customers)
- https://platform.claude.com/docs/en/manage-claude/api-and-data-retention

> **This is not legal or compliance advice.** BAA scope and feature eligibility
> change over time and vary by plan, cloud platform, and configuration. Verify your
> organization's current coverage with the relevant provider's official
> documentation, and **clear any real-data workflow with your IRB / privacy /
> security office before using PHI.**

---

## 5. Checklist

**Phase A — development (no PHI):**
- [ ] Dev data is synthetic (`synthetic_clif`) or an approved de-identified demo.
- [ ] No real `data_directory` / config path is shared with the agent.
- [ ] The config used with the agent points only at the non-PHI output folder.
- [ ] No raw tracebacks, dataframe previews, IDs, dates, or note text from real data
      are pasted into the conversation.
- [ ] Small-cell counts are suppressed or aggregated.

**Phase B — before real data touches Claude (verification gate):**
- [ ] Active credential verified as the **covered API key / cloud endpoint**, not
      the Max/Pro subscription (checked via `/status` + env vars).
- [ ] Deployment covered by a signed BAA (Anthropic for API/Enterprise; AWS/GCP for
      Bedrock/Vertex); **ZDR on if using Claude Code** (the first-party API on a
      HIPAA-ready org does not require ZDR — separate orgs).
- [ ] The specific **model** is a Covered Model for the route (not a Fable/Mythos
      model excluded under Claude Code / Cowork).
- [ ] Current org coverage re-verified against the official docs (facts are
      perishable and org-specific).
- [ ] IRB / privacy / security sign-off obtained for the real-data run.
- [ ] **Even on the covered channel, outputs are still sanitized (§3)** — a BAA is
      not permission to paste raw PHI or raw tracebacks.

---

## 6. CLIF version: 2.1 (stable) vs 3.0 (multimodal), and the toggle

<!-- PLANNER NOTE (not user-facing guidance): the skill-wide "CLIF 2.1.1" currency
     claim is UNVERIFIED against a published CLIF tag (no 2.1.1 tag found via
     ref/tavily 2026-07-22; the official data dictionary version is 2.1.0). Do NOT
     resolve that claim here — it is owned by the separate v2.1.1-currency PR (#2).
     Version reconciliation lives in SKILL.md's version block.
     The 2.1↔3.0 facts below were verified via clifpy docs + the CLIF consortium
     data dictionary on 2026-07-23 — re-verify before relying (3.0 is stabilizing). -->

### The `CLIF_SCHEMA_VERSION` toggle

Set the `CLIF_SCHEMA_VERSION` environment variable to declare which CLIF version the
data (and therefore your code) targets:

| Value | Meaning |
|-------|---------|
| `2.1` (default) | Current stable data dictionary; what `synthetic_clif` and MIMIC-IV-Ext-CLIF emit. |
| `3.0` | Breaking multimodal release (July 2026). Adds imaging + clinical-notes tables; lowercase/`snake_case` category conventions; several tables still **Alpha**. |

**Ask the researcher which version their real data is in before writing analysis code** —
the category/value conventions and the table set differ, so code written for one version
will mis-filter or fail validation against the other. The example scripts read this
variable and echo the value you set so a wrong declaration is easy to spot; the echo
reflects only your self-declaration and performs **no** automated version detection. On
the `3.0` path the scripts additionally warn that their category filters use 2.1-convention
values (uncorrected for 3.0) and may silently match zero rows — because they do not
crosswalk, a stale filter fails quietly rather than loudly.

### Dev sandboxes are CLIF 2.1

`synthetic_clif` emits **CLIF 2.1.0** — stand up a sandbox with one command via
[`scripts/setup_dev_data.sh`](../scripts/setup_dev_data.sh), then load it with
`ClifOrchestrator(config_path=...)`. (clifpy is **not** confirmed to ship a bundled
demo-data loader — see §1; if your installed version does, prefer it, but don't assume
`clifpy.data.load_demo_clif` exists.)

It is **dev-safe for code authoring**: `clifpy`'s `2.1` schemas validate 2.1 data, so
an agent can write and exercise your code against it. Don't treat `synthetic_clif`'s
microbiology-organism or lab groupings as canonical — the authority is this skill's
[`mCIDE/`](../mCIDE/) and [`schemas/`](../schemas/) files. Validation may surface grouping
deltas against your target version; those are expected data-dictionary differences, not
code bugs.

### Migrating 2.1 → 3.0 (a deliberate, audited step — not automatic)

`clifpy` ships **both** the 2.1 and 3.0 schemas. There is **no version switch on
`ClifOrchestrator`**; you migrate values or validate against an explicit version.
Migration lowercases/`snake_case`s categorical values (`IMV` → `imv`, `Non-Hispanic` →
`non_hispanic`) and applies curated renames (`High Flow NC` → `hfnc`) — verified against
the clifpy migration guide on 2026-07-23:

```python
# Whole site (every beta table) — audit first with dry_run.
from clifpy.utils.migrate_versions_2_1_to_3 import CrosswalkMigrationRunner
CrosswalkMigrationRunner(config_path="your_site.yaml").run(dry_run=True)

# One in-memory table — returns (converted_df, report).
from clifpy import crosswalk_table_2_1_to_3_0
converted, report = crosswalk_table_2_1_to_3_0(co.respiratory_support.df, "respiratory_support")

# Out-of-core (file too large for memory):
from clifpy import crosswalk_file_2_1_to_3_0

# Validate a DataFrame against a specific version's schema:
from clifpy.schemas import load_schema
from clifpy.utils import validator
errors = validator.validate_dataframe(converted, load_schema("respiratory_support", "3.0"))
```

- **`report` is structured — read it.** It flags **ambiguous** values that no rule can
  resolve (e.g. `albumin` → `albumin_5` vs `albumin_25`, by product concentration). A
  human with domain knowledge resolves these; **an agent must not guess them.**
- **Do not double-convert.** The crosswalk is 2.1 → 3.0. Data already in 3.0 (or loaded
  from a 3.0 source) must not be run through it again. This is why the scripts *declare*
  a version rather than blindly crosswalking on load.
- **Confirm your installed clifpy exposes the entry points used above** (recent builds ship
  the 3.0 schemas and crosswalk; older ones do not — these imports fail loudly with
  `ImportError` if absent, so verify before relying on them):
  `python -c "from clifpy import crosswalk_table_2_1_to_3_0, crosswalk_file_2_1_to_3_0; from clifpy.utils.migrate_versions_2_1_to_3 import CrosswalkMigrationRunner; from clifpy.schemas import load_schema; from clifpy.utils import validator"`.

### 3.0 is multimodal — the PHI stakes go up

CLIF 3.0 adds **imaging** and **clinical notes**, the most PHI-dense data in the format.
By design CLIF stores only note **metadata** in `clinical_notes_facts` — **the note text
itself is not held in CLIF** (just-in-time provisioning). Mirror that discipline: the
sanitization rules in §3 apply *doubly* to notes and imaging. A watching agent must never
receive note text, image pixels, or DICOM metadata (which carries names, dates, and can
contain burned-in identifiers). Several 3.0 tables are **Alpha** ("changes remain likely"),
so treat the [3.0 data dictionary](https://clif-icu.com/data-dictionary/data-dictionary-3.0.0)
as the authority over any snapshot in this skill.

Your **real data remains the source of truth**; the synthetic/demo cohorts are development
sandboxes only.

---

## Related Documentation

| Topic | File |
|-------|------|
| Config file setup / loading options | [clifpy_utils/configuration.md](clifpy_utils/configuration.md) |
| Dev-sandbox bootstrapper | [../scripts/setup_dev_data.sh](../scripts/setup_dev_data.sh) |
| Skill overview & PHI-safe summary | [../SKILL.md](../SKILL.md) |
