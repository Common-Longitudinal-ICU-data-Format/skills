# clifpy API Reference

## Installation

```bash
pip install clifpy
```

---

## Loading Tables (Preferred Method)

**Always use individual table classes. Only use ClifOrchestrator for wide datasets.**

### Basic Pattern
```python
from clifpy.tables import Vitals, Labs, Hospitalization

hosp_ids = ['H001', 'H002', 'H003']

table = Vitals.from_file(
    data_directory='/path/to/data',
    filetype='parquet',           # or 'csv'
    timezone='US/Eastern',
    filters={
        'hospitalization_id': hosp_ids,
        'vital_category': ['heart_rate', 'sbp']  # Long tables: filter by category
    },
    columns=['hospitalization_id', 'vital_category', 'vital_value', 'recorded_dttm'],  # Optional
    sample_size=1000              # Optional: for testing
)

df = table.df  # Access DataFrame
```

### All Table Classes
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

## from_file() Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| data_directory | str | Path to CLIF data files |
| filetype | str | 'parquet' or 'csv' |
| timezone | str | e.g., 'US/Eastern', 'UTC' |
| filters | dict | **Required.** `{'hospitalization_id': ids, 'category_col': values}` |
| columns | list | Optional. Limit columns loaded |
| sample_size | int | Optional. Limit rows for testing |
| config_path | str | Optional. Path to config YAML/JSON |
| output_directory | str | Optional. For validation output |
| verbose | bool | Optional. Show loading messages |

---

## ClifOrchestrator (Only for Wide Datasets)

Use **only** when you need:
- `create_wide_dataset()`
- Multi-table operations

```python
from clifpy import ClifOrchestrator

co = ClifOrchestrator(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern'
)

# Load with filters
co.load_table('vitals', filters={'hospitalization_id': hosp_ids})
co.load_table('labs', filters={'hospitalization_id': hosp_ids})

# Access
vitals_df = co.vitals.df
labs_df = co.labs.df
```

---

## Validation

```python
# Run validation
table.validate()

# Check if valid
if table.isvalid():
    print("Valid")
else:
    print(f"Errors: {len(table.errors)}")
    for error in table.errors:
        print(error)

# Get summary
summary = table.get_summary()
```

---

## Table-Specific Methods

### Hospitalization
```python
hosp = Hospitalization.from_file(...)
hosp.calculate_length_of_stay()  # Adds LOS column
hosp.get_mortality_rate()        # Returns mortality %
hosp.get_summary_stats()         # Age, LOS, mortality stats
```

### Labs
```python
labs = Labs.from_file(...)
labs.get_lab_reference_units()       # Units by category
labs.standardize_reference_units()   # Normalize unit strings
labs.get_lab_category_stats()        # Stats per category
```

### RespiratorySupport
```python
resp = RespiratorySupport.from_file(...)
resp_filled = resp.waterfall(bfill=False)  # Forward-fill data
```

### Adt
```python
adt = Adt.from_file(...)
adt.check_overlapping_admissions()  # Find overlapping locations
```

### MicrobiologyCulture
```python
culture = MicrobiologyCulture.from_file(...)
culture.validate_timestamp_order()   # order_dttm <= collect_dttm <= result_dttm
culture.organism_cat_name_map()      # Category to names mapping
```

### HospitalDiagnosis
```python
dx = HospitalDiagnosis.from_file(...)
dx.get_diagnosis_summary()           # Summary stats
dx.get_primary_diagnosis_counts()    # Primary dx counts
dx.get_poa_statistics()              # Present-on-admission stats
```

---

## Config File

```yaml
# config.yaml
data_directory: "/path/to/clif/data"
filetype: "parquet"
timezone: "US/Eastern"
output_directory: "output"
```

```python
from clifpy.utils import load_config

config = load_config('config.yaml')
```
