---
name: clif
description: Use for ICU clinical data analysis - loading CLIF tables with clifpy, filtering by hospitalization_id and category, computing SOFA/CCI scores, creating wide datasets
---

# CLIF + clifpy

**CLIF** (Common Longitudinal ICU data Format) + **clifpy** Python library for ICU data analysis.

```bash
pip install clifpy
```

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

## What Are You Doing?

| Task | Reference |
|------|-----------|
| Load specific table(s) | [tables.md](reference/tables.md) |
| Check available categories | [tables.md](reference/tables.md) |
| Use clifpy API | [clifpy-api.md](reference/clifpy-api.md) |
| Compute SOFA, CCI, Elixhauser | [clinical-scores.md](reference/clinical-scores.md) |
| Create wide dataset, waterfall | [data-processing.md](reference/data-processing.md) |
| Look up mCIDE values | [mCIDE/](mCIDE/) CSV files |

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
