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

## Critical: Always Filter Data

1. **hospitalization_id** - Filter ALL tables
2. **Category filters** - Filter long tables by category column:

| Table | Category Column | Example Values |
|-------|-----------------|----------------|
| vitals | vital_category | heart_rate, sbp, spo2, temp_c |
| labs | lab_category | hemoglobin, creatinine, lactate |
| patient_assessments | assessment_category | gcs_total, rass, cam_icu |
| medication_admin_continuous | med_category | norepinephrine, propofol, fentanyl |
| medication_admin_intermittent | med_category | vancomycin, cefepime |
| respiratory_support | device_category | IMV, NIPPV, High_Flow_NC |

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

## Reference Files

For detailed information, read the appropriate reference file:

| Topic | File | When to Read |
|-------|------|--------------|
| **Table schemas & categories** | [reference/tables.md](reference/tables.md) | Looking up table structure, column definitions, category values |
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
