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

---

## Reference Files

For detailed information, read the appropriate reference file:

| Topic | File | When to Read |
|-------|------|--------------|
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
