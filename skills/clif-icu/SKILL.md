---
name: clif-icu
description: Write, debug, and review CLIF analytical code in R or Python. Confirm the user's CLIF and mCIDE version, retrieve matching GitHub vocabularies, catch case/snake_case and schema bugs, and check macOS/Linux/Windows portability. Use in any coding harness with synthetic data and privacy-safe outputs.
---

# CLIF + clifpy

**CLIF** (Common Longitudinal ICU data Format) analytics in **R or Python**.
Use the active harness's tools in Codex, Claude Code, OpenCode, Pi, or another
coding agent. Read [portable agentic coding](reference/agentic-coding.md) before
writing code. Claude plugin hooks and agents are optional, harness-specific integrations.

For Python with clifpy, install it in the project's environment. R workflows use
the project's R dependencies; they do not require a Python API.

---

## Critical: PHI/PII-safe agentic development

These rules apply to every harness, model, language, and OS.

1. **Develop against synthetic data only.** Never expose real patient rows,
   identifiers, dates, notes, images, secrets, or embedded sensitive examples to
   the model, tool output, MCP, web searches, external services, or telemetry.
   Local execution can still expose stdout and tracebacks to the agent.
2. **The researcher runs real-data analyses separately**, in their approved
   environment with the agent absent. Do not move real data into a coding
   workspace or synced output folder to make a test pass.
3. **Share only privacy-reviewed aggregate outputs**, with appropriate
   suppression. Do not paste raw tracebacks, previews, patient identifiers,
   arbitrary free-text labels, or small-cell counts.
4. **Check the active harness's protections.** Claude plugin hooks are optional
   defense in depth, not a sandbox, a BAA, or a compliance guarantee. Their
   absence never permits sensitive-data access in another harness.

For a synthetic sandbox, use [synthetic_clif](https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif)
or [clif-forge](https://github.com/sajor2000/clif-forge); see
[synthetic datasets](reference/synthetic-datasets.md) and
[PHI-safe development](reference/phi-safe-development.md). A credentialed or
real-derived dataset is not automatically safe for an agent session.

---

## Confirm the CLIF and mCIDE version

**Ask the user which data-dictionary version their tables follow before writing
version-sensitive analysis code.** Require an explicit answer or an existing
project declaration. Do not default to 2.1, infer a version from casing, or
silently upgrade the dataset. If undeclared, continue public-source research
and environment checks while the version question is pending.

Use the declared version, whether 2.1, 3.0, or a future release, and retrieve its
[current mCIDE and schemas](reference/current-mcide.md). CLIF 2.1 uses mixed-case
values; 3.0 standardizes many values to lowercase `snake_case` and also renames
categories. Verify actual sources instead of applying a generic case conversion.

`CLIF_SCHEMA_VERSION` in bundled examples declares a target; it does not detect,
validate, or migrate the input. Legacy examples may support only named versions.
Verify their filters and installed APIs before reuse. The clifpy package version
and CLIF data version are separate. Migration requires an explicit, reviewed map.

---

## When to Use This Skill

Activate this skill when:
- Working with ICU/intensive care unit clinical data
- Using or asking about the CLIF data format
- Writing or debugging CLIF analyses in R or Python with any coding harness
- Loading data with the clifpy Python library
- Computing clinical scores (SOFA, CCI, Elixhauser, MDRO)
- Processing vitals, labs, medications, or respiratory support data
- Creating wide datasets from longitudinal ICU data
- Researching sepsis, ARDS, or critical care outcomes
- Reviewing CLIF code for macOS, Linux, and Windows compatibility
- Checking CLIF 2.1/3.0 table, field, and category capitalization compatibility

---

## Instructions

Follow these steps when working with CLIF data:

0. **Confirm the target** - Record the user's CLIF version and mCIDE ref, language, runtime, OS, and harness. Read [agentic coding](reference/agentic-coding.md) and retrieve [current mCIDE](reference/current-mcide.md).
1. **Identify required tables** - Determine which CLIF tables contain the data needed (vitals, labs, medications, etc.)
2. **Validate keys and restrict the cohort** - Use `patient_id` for patient-level tables and `hospitalization_id` where the declared schema supports it. Audit and canonicalize categorical inputs before applying category filters; raw pushdown filters can discard nonconforming variants.
3. **Choose the right approach** - Follow the project's R or Python stack. For Python/clifpy:
   - Use **individual table classes** for most tasks (faster, more memory efficient)
   - Use **ClifOrchestrator** only when creating wide datasets or computing SOFA scores
4. **Audit categories before filtering** - Use the declared version's current schema and mCIDE. Check mixed case, spacing, unknowns, and collisions before a category predicate can discard rows. Preserve originals and use unambiguous canonical mappings. Bundled [mCIDE/](mCIDE/) values are snapshots; see the [compatibility guide](reference/compatibility-review.md).
5. **Compute clinical scores** - For Python/clifpy, verify the installed SOFA/CCI/Elixhauser interfaces. In R, verify the chosen implementation and synthetic score tests; do not invent R equivalents of Python methods. See [clinical scores](reference/clinical-scores.md).
6. **Review compatibility** - Follow [reference/compatibility-review.md](reference/compatibility-review.md). Check case, whitespace, `snake_case`, schema conformance, and OS portability. Repair only unambiguous vocabulary-backed mismatches, preserve source values, and make unknowns visible. Test expected results with synthetic inputs; report executed and untested targets.

---

## Critical: Always Filter Data

### Long Tables (Use BOTH hospitalization_id AND category filters)

These tables have many rows per hospitalization. Restrict the cohort first, then
validate/normalize categorical values before applying category filters. Do not
push a raw category predicate into the loader when it can discard nonconforming
variants or hide unknowns. Use canonical filters once that input contract is verified:

| Table | Category Column | Example Values |
|-------|-----------------|----------------|
| vitals | vital_category | heart_rate, sbp, spo2, temp_c |
| labs | lab_category | hemoglobin, creatinine, lactate |
| patient_assessments | assessment_category | gcs_total, rass, cam_icu |
| medication_admin_continuous | med_category | norepinephrine, propofol, fentanyl |
| medication_admin_intermittent | med_category | vancomycin, cefepime |
| respiratory_support | device_category | 2.1: IMV, NIPPV, High Flow NC; 3.0: imv, nippv, hfnc |
| microbiology_culture | organism_category | staphylococcus_aureus, escherichia_coli |

### Other Tables (use the schema's cohort key)

Filter patient-level tables by `patient_id`; use `hospitalization_id` for encounter-level tables where that column exists. Verify table and field names against the declared CLIF version before applying a cohort filter.

---

## Quick Start (Python/clifpy)

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
| **Portable agentic coding** | [reference/agentic-coding.md](reference/agentic-coding.md) | R/Python workflows, harness differences, and PHI/PII boundaries |
| **Current mCIDE** | [reference/current-mcide.md](reference/current-mcide.md) | Resolving the user's declared CLIF version to current GitHub vocabulary and schemas |
| **Code compatibility review** | [reference/compatibility-review.md](reference/compatibility-review.md) | Writing/reviewing CLIF code for macOS/Linux/Windows and CLIF 2.1/3.0, especially capitalization |
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
2. **Filter with the table's actual cohort key**
3. **Filter long tables by category**
4. **Use parquet** - Faster than CSV
5. **Limit columns** - `columns=['col1', 'col2']`

---

## Requirements

- Use the project's supported R or Python runtime and locked dependencies.
- For Python/clifpy, verify the installed package's runtime and dependency requirements.
- Shell helpers require their documented shell; do not assume native Windows can run `.sh` files.
- **For agent-assisted development:** use supplied or in-memory synthetic fixtures. The Bash sandbox helper is optional; see [PHI-safe development](reference/phi-safe-development.md). Do not run against real patient data while an agent can observe.
