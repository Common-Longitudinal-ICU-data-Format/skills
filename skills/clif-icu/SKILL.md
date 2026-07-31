---
name: clif-icu
description: Analyzes ICU clinical data using the Common Longitudinal ICU data Format (CLIF) and clifpy Python library. Loads and filters CLIF tables (vitals, labs, medications, respiratory support, microbiology) by hospitalization_id and category columns. Computes clinical scores including SOFA, Charlson Comorbidity Index (CCI), and Elixhauser. Creates wide datasets and performs data transformations. Use when working with ICU data, CLIF format, clifpy, clinical scoring, ventilator data, sepsis research, or intensive care analytics.
---

# CLIF + clifpy

**CLIF** (Common Longitudinal ICU data Format) + **clifpy** Python library for ICU data analysis.

```bash
pip install clifpy
```

---

## Critical: PHI-Safe Agentic Development

**When any AI agent helps write or debug CLIF code — clifpy, R, ETL, ad-hoc scripts, anything — the agent must never receive PHI/RHI (real patient data).** This is a universal rule for CLIF agentic coding, not just clif-icu analysis. Develop against non-PHI data; the researcher runs on real data themselves, in their own secure environment.

1. **Develop against non-PHI data.** The agent writes/debugs code against synthetic or demo CLIF data only. If your org has **Claude Enterprise**, use it here too; but **any channel — a consumer Max/Pro plan or the first-party API — is fine here, because the agent never sees PHI.** A covered channel becomes required only at step 3.
2. **The researcher runs the code on real PHI themselves**, in their own secure/HIPAA environment. The strongest posture keeps the agent absent for this step.
3. **If Claude must be in the loop on real data, toggle to a BAA-covered channel first.** Which channels are covered — and their per-channel conditions (ZDR, HIPAA-ready org, cloud-provider BAA) — is perishable; the current matrix, with its verify-before-relying timestamp, lives in [reference/phi-safe-development.md](reference/phi-safe-development.md). **Verify the active credential is the covered endpoint, not a Max/Pro plan** (e.g. `/status` + env vars), confirm current org coverage there, and **sanitize outputs regardless — a covered channel is not permission to paste raw PHI.**
4. **This skill self-enforces the above** within clif-icu work — pointing an agent at real data on an uncovered plan is a defect.

**Non-PHI dev data:** Choose from [`synthetic_clif`](https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif), [`clif-forge`](https://github.com/sajor2000/clif-forge), or [MIMIC-IV-Ext-CLIF](https://physionet.org/content/mimic-iv-ext-clif/1.1.0/) — see [`reference/synthetic-datasets.md`](reference/synthetic-datasets.md) for a comparison. [`scripts/setup_dev_data.sh`](scripts/setup_dev_data.sh) bootstraps a one-command sandbox.

**Never paste PHI into the conversation** — no raw tracebacks, `.head()`/`.sample()`/`value_counts()` previews, MRNs, `patient_id`/`hospitalization_id` values, dates/timestamps, note or organism free text, or small-cell counts from real data. This holds even on a BAA-covered channel.

Full setup, sanitization checklist, and HIPAA-channel guidance: [reference/phi-safe-development.md](reference/phi-safe-development.md).

---

## CLIF version: 2.1 (stable) vs 3.0 (multimodal)

**Default to CLIF 2.1.0** — the current stable data dictionary, and what clifpy and
`synthetic_clif` target. **CLIF 3.0** is a *breaking, major* release (July 2026) that
goes **multimodal**: it adds imaging and clinical-notes tables (e.g. `clinical_notes_facts`,
`airway`) and renames many `*_category`/`*_group`/`*_type` values to a lowercase/`snake_case`
convention (`IMV` → `imv`, `High Flow NC` → `hfnc`). Several 3.0 tables are still **Alpha**
("changes remain likely") — treat the [3.0 data dictionary](https://clif-icu.com/data-dictionary/data-dictionary-3.0.0)
as the authority, not this file. *(Verified 2026-07-23; re-check before relying.)*

**Toggle:** set the `CLIF_SCHEMA_VERSION` environment variable to `2.1` (default) or
`3.0`. **Ask the researcher which CLIF version their data is in before writing code** —
the value conventions and table set differ.

**clifpy ships both schemas.** It does not switch version on `ClifOrchestrator`; instead
you migrate or validate against an explicit version. Migrate 2.1 → 3.0 with
`crosswalk_table_2_1_to_3_0(df, table)` (in memory), `crosswalk_file_2_1_to_3_0(...)`
(out-of-core), or `CrosswalkMigrationRunner(config_path=...).run(dry_run=True)` (whole
site); validate against a version with `load_schema(table, "3.0")`. Some values are
**ambiguous** and need a human decision (e.g. `albumin` → `albumin_5`/`albumin_25`) —
never let an agent auto-resolve those. Full details and code:
[reference/phi-safe-development.md](reference/phi-safe-development.md).

**PHI note:** 3.0's clinical notes and imaging are the *most PHI-dense* data in CLIF. By
design CLIF holds only note **metadata** (the text is provisioned just-in-time, not stored
in CLIF) — mirror that discipline: the PHI-safe rules above apply *doubly* to notes and
imaging, which an agent must never receive.

---

## When to Use This Skill

Activate this skill when:
- Working with ICU/intensive care unit clinical data
- Using or asking about the CLIF data format
- Loading data with the clifpy Python library
- Computing clinical scores (SOFA, CCI, Elixhauser, MDRO)
- Processing vitals, labs, medications, or respiratory support data
- Creating wide datasets from longitudinal ICU data
- Researching sepsis, ARDS, or critical care outcomes

---

## Instructions

Follow these steps when working with CLIF data:

1. **Identify required tables** - Determine which CLIF tables contain the data needed (vitals, labs, medications, etc.)
2. **Always filter data** - Use hospitalization_id filters on all tables; add category filters on long tables (see filtering rules below)
3. **Choose the right approach**:
   - Use **individual table classes** for most tasks (faster, more memory efficient)
   - Use **ClifOrchestrator** only when creating wide datasets or computing SOFA scores
4. **Look up category values** - Check [mCIDE/](mCIDE/) for valid category values before filtering
5. **Compute clinical scores** - Use ClifOrchestrator for SOFA, or refer to [reference/clinical-scores.md](reference/clinical-scores.md) for CCI and Elixhauser

---

## Critical: Always Filter Data

### Long Tables (Use BOTH hospitalization_id AND category filters)

These tables have many rows per hospitalization. **Always filter by category column:**

| Table | Category Column | Example Values |
|-------|-----------------|----------------|
| vitals | vital_category | heart_rate, sbp, spo2, temp_c |
| labs | lab_category | hemoglobin, creatinine, lactate |
| patient_assessments | assessment_category | gcs_total, rass, cam_icu |
| medication_admin_continuous | med_category | norepinephrine, propofol, fentanyl |
| medication_admin_intermittent | med_category | vancomycin, cefepime |
| respiratory_support | device_category | IMV, NIPPV, High_Flow_NC |
| microbiology_culture | organism_category | staphylococcus_aureus, escherichia_coli |

### Other Tables (hospitalization_id filter only, if needed)

All other tables (patient, hospitalization, adt, code_status, position, crrt_therapy, ecmo_mcs, hospital_diagnosis, patient_procedures, microbiology_susceptibility, microbiology_nonculture) have fewer rows per hospitalization. Filter by `hospitalization_id` only when needed.

---

## Quick Start

> **PHI-safe:** for agent-assisted work, `data_directory` must point at **non-PHI** synthetic/demo data — see [reference/phi-safe-development.md](reference/phi-safe-development.md).

### Load Individual Tables (Preferred)
```python
from clifpy.tables import Vitals, Labs, PatientAssessments

hosp_ids = ['H001', 'H002', 'H003']

# Always filter by BOTH hospitalization_id AND category
vitals = Vitals.from_file(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern',
    filters={
        'hospitalization_id': hosp_ids,
        'vital_category': ['heart_rate', 'sbp', 'spo2']
    }
)

labs = Labs.from_file(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern',
    filters={
        'hospitalization_id': hosp_ids,
        'lab_category': ['hemoglobin', 'creatinine', 'lactate']
    }
)

# Access DataFrames
vitals_df = vitals.df
labs_df = labs.df
```

### ClifOrchestrator (Only for Wide Datasets)
```python
from clifpy import ClifOrchestrator

# PHI-safe: with an agent, point data_directory at non-PHI synthetic/demo data.
co = ClifOrchestrator(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern'
)
co.load_table('vitals', filters={'hospitalization_id': hosp_ids})
```

---

## Example Scripts

Complete workflow examples in [scripts/](scripts/):

### cohort_identification_example.py
End-to-end cohort identification workflow:
1. Load core tables (patient, hospitalization, adt)
2. Filter adults (age >= 18) and date range (2018-2024)
3. Stitch encounters using 6-hour windows
4. Identify CRRT encounters
5. Exclude ESRD patients (ICD codes N185, N186, Z992)
6. Check weight data availability
7. Build final cohort with demographics
8. Save to parquet

```python
from clifpy.clif_orchestrator import ClifOrchestrator
from clifpy.utils.stitching_encounters import stitch_encounters
```

### sofa_score_calculation.py
SOFA score computation workflow:
1. Load cohort and define time windows (e.g., first 24h)
2. Load required tables (labs, vitals, assessments, medications, respiratory)
3. Clean medication data (remove null doses)
4. Convert vasopressor units to mcg/kg/min
5. Create wide dataset with `REQUIRED_SOFA_CATEGORIES_BY_TABLE`
6. Compute 6 SOFA components (respiratory, coagulation, liver, cardiovascular, CNS, renal)
7. Save results to CSV

```python
from clifpy.clif_orchestrator import ClifOrchestrator
from clifpy.utils.sofa import REQUIRED_SOFA_CATEGORIES_BY_TABLE
```

### setup_dev_data.sh
Dev-environment bootstrapper (not an analysis workflow). Clones [`synthetic_clif`](https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif), installs it, generates a small **non-PHI** CLIF cohort into `./dev_data`, and writes a `clif_demo_config.json` — a one-command sandbox that is safe to share with an agent. Use this so the agent never needs to touch real PHI (see [reference/phi-safe-development.md](reference/phi-safe-development.md)).

```bash
scripts/setup_dev_data.sh              # synthetic_clif -> ./dev_data + clif_demo_config.json
```

---

## Reference Files

For detailed information, read the appropriate reference file:

| Topic | File | When to Read |
|-------|------|--------------|
| **PHI-safe agentic development** | [reference/phi-safe-development.md](reference/phi-safe-development.md) | Before pointing an agent at any data; setting up a non-PHI dev environment; sanitizing real-data errors |
| **Table schemas & categories** | [reference/tables.md](reference/tables.md) | Looking up table structure, column definitions, category values |
| **Clinical scores** | [reference/clinical-scores.md](reference/clinical-scores.md) | Computing SOFA, CCI, Elixhauser scores |
| **Data processing** | [reference/data-processing.md](reference/data-processing.md) | Wide datasets, hourly aggregation, encounter stitching, outlier handling |
| **clifpy API** | [reference/clifpy-api.md](reference/clifpy-api.md) | Complete API reference for clifpy library |
| **CLIF vocabulary** | [mCIDE/](mCIDE/) | Looking up specific category values and their descriptions |
| **Config file setup** | [reference/clifpy_utils/configuration.md](reference/clifpy_utils/configuration.md) | Setting up clif_config.json, understanding loading options |
| **Table classes & methods** | [reference/clifpy_utils/table_classes.md](reference/clifpy_utils/table_classes.md) | Using BaseTable, from_file(), table-specific methods |
| **ClifOrchestrator usage** | [reference/clifpy_utils/orchestrator.md](reference/clifpy_utils/orchestrator.md) | Wide datasets, SOFA scores, encounter stitching |
| **Utility functions** | [reference/clifpy_utils/clifpy_functions.md](reference/clifpy_utils/clifpy_functions.md) | Understanding internal clifpy logic, custom implementations |
| **YAML schemas** | [schemas/](schemas/) | Column definitions, data types, validation rules |

---

## All Table Classes

```python
from clifpy.tables import (
    Patient, Hospitalization, Adt,
    Vitals, Labs, RespiratorySupport, Position,
    MedicationAdminContinuous, MedicationAdminIntermittent,
    PatientAssessments, HospitalDiagnosis,
    CodeStatus, CrrtTherapy, EcmoMcs,
    MicrobiologyCulture, MicrobiologyNonculture, MicrobiologySusceptibility,
    PatientProcedures
)
```

---

## Performance Rules

1. **Use individual table classes** - Not ClifOrchestrator
2. **ALWAYS filter by hospitalization_id**
3. **Filter long tables by category**
4. **Use parquet** - Faster than CSV
5. **Limit columns** - `columns=['col1', 'col2']`

---

## Requirements

```bash
pip install clifpy
```

- Python 3.8+
- Dependencies: pandas, pyarrow (for parquet support)
- **For agent-assisted development:** set up a non-PHI dataset first (`scripts/setup_dev_data.sh`; see [reference/phi-safe-development.md](reference/phi-safe-development.md)). Do not run against real PHI while an agent can see the output.
