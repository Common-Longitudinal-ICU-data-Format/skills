# ClifOrchestrator Reference

The `ClifOrchestrator` is the central class for managing multiple CLIF tables with consistent configuration.

## Basic Usage

```python
from clifpy import ClifOrchestrator

# Initialize with config file
co = ClifOrchestrator(config_path="clif_config.json")

# Load specific tables
co.initialize(tables=['patient', 'hospitalization', 'vitals', 'labs'])

# Access loaded tables
vitals_df = co.vitals.df
labs_df = co.labs.df

# Validate all loaded tables
co.validate_all()
```

---

## Initialization Options

```python
ClifOrchestrator(
    config_path=None,           # Path to config file
    data_directory=None,        # Direct param (overrides config)
    filetype=None,              # Direct param (overrides config)
    timezone=None,              # Direct param (overrides config)
    output_directory=None,      # Direct param (overrides config)
    stitch_encounter=False,     # Enable encounter stitching
    stitch_time_interval=6      # Hours between encounters to stitch
)
```

---

## Key Methods

| Method | Description |
|--------|-------------|
| `initialize(tables=[...])` | Load multiple tables at once |
| `load_table(table_name)` | Load a single table |
| `get_loaded_tables()` | List currently loaded table names |
| `validate_all()` | Validate all loaded tables |
| `create_wide_dataset(...)` | Create wide time-series dataset |
| `convert_wide_to_hourly(...)` | Aggregate to hourly windows |
| `compute_sofa_scores(...)` | Calculate SOFA scores |
| `run_stitch_encounters()` | Stitch related hospitalizations |
| `convert_dose_units_for_continuous_meds(...)` | Convert medication units |
| `get_sys_resource_info()` | Get system CPU/memory info |

---

## Loading with Filters

Filter data at load time for efficiency:

```python
co.initialize(
    tables=['vitals', 'labs'],
    filters={
        'vitals': {
            'hospitalization_id': ['H001', 'H002'],
            'vital_category': ['heart_rate', 'sbp', 'spo2']
        },
        'labs': {
            'hospitalization_id': ['H001', 'H002'],
            'lab_category': ['sodium', 'creatinine', 'lactate']
        }
    }
)
```

---

## Creating Wide Dataset

Combine multiple tables into wide time-series format:

```python
co.create_wide_dataset(
    tables_to_load=['vitals', 'labs', 'respiratory_support'],
    category_filters={
        'vitals': ['heart_rate', 'sbp', 'spo2'],
        'labs': ['sodium', 'creatinine', 'lactate'],
        'respiratory_support': ['device_category', 'fio2_set']
    },
    hospitalization_ids=['H001', 'H002'],  # Optional: filter to specific IDs
    sample=False,                           # True for random 20 sample
    batch_size=1000,                        # Process in batches
    show_progress=True                      # Show progress bars
)

# Access result
wide_df = co.wide_df
print(wide_df.shape)  # (rows, columns)
```

### category_filters Parameter

For **pivot tables** (vitals, labs, medications, assessments):
- Values are **category values** to filter and pivot into columns
- Example: `'vitals': ['heart_rate', 'sbp']` creates columns `heart_rate`, `sbp`

For **wide tables** (respiratory_support):
- Values are **column names** to keep from the table
- Example: `'respiratory_support': ['device_category', 'fio2_set']`

---

## Hourly Aggregation

Convert wide dataset to hourly windows:

```python
# Create wide dataset first
co.create_wide_dataset(...)

# Aggregate to hourly windows
hourly_df = co.convert_wide_to_hourly(
    aggregation_config={
        'mean': ['heart_rate', 'sbp'],
        'max': ['spo2'],
        'min': ['map'],
        'first': ['gcs_total'],
        'boolean': ['norepinephrine'],      # True if any non-zero
        'one_hot_encode': ['device_category']
    },
    id_name='hospitalization_id',  # or 'encounter_block'
    hourly_window=1,               # 1-hour windows
    fill_gaps=False                # True to fill empty windows with NaN
)
```

---

## SOFA Score Calculation

```python
# Compute SOFA scores
sofa_df = co.compute_sofa_scores(
    extremal_type='worst',          # Use worst values per encounter
    id_name='encounter_block',      # Group by encounter blocks
    fill_na_scores_with_zero=True   # Missing = 0 (normal organ function)
)

# Access result
print(sofa_df.columns)
# ['encounter_block', 'sofa_respiratory', 'sofa_coagulation',
#  'sofa_liver', 'sofa_cardiovascular', 'sofa_cns',
#  'sofa_renal', 'sofa_total']
```

---

## Encounter Stitching

Group related hospitalizations (e.g., ED to inpatient transfers):

```python
co = ClifOrchestrator(
    config_path="config.json",
    stitch_encounter=True,
    stitch_time_interval=6  # 6 hours
)

# Or stitch manually
co.run_stitch_encounters()

# Access encounter mapping
mapping = co.get_encounter_mapping()
# DataFrame with hospitalization_id -> encounter_block
```

---

## Medication Unit Conversion

Convert dose units to standard format:

```python
co.convert_dose_units_for_continuous_meds(
    preferred_units={
        'norepinephrine': 'mcg/kg/min',
        'propofol': 'mcg/kg/min',
        'fentanyl': 'mcg/kg/hr'
    },
    hospitalization_ids=['H001', 'H002'],  # Optional filter
    save_to_table=True  # Store in medication_admin_continuous.df_converted
)
```

---

## Accessing Loaded Tables

After loading, tables are accessible as attributes:

```python
co.initialize(tables=['patient', 'hospitalization', 'vitals'])

# Access as table objects
co.patient           # Patient table object
co.hospitalization   # Hospitalization table object
co.vitals            # Vitals table object

# Access DataFrames
co.patient.df        # Patient DataFrame
co.vitals.df         # Vitals DataFrame

# List loaded tables
co.get_loaded_tables()  # ['patient', 'hospitalization', 'vitals']
```

---

## Available Tables

All 18 CLIF tables can be loaded:

```python
co.initialize(tables=[
    'patient',
    'hospitalization',
    'adt',
    'vitals',
    'labs',
    'medication_admin_continuous',
    'medication_admin_intermittent',
    'patient_assessments',
    'respiratory_support',
    'position',
    'hospital_diagnosis',
    'microbiology_culture',
    'microbiology_susceptibility',
    'microbiology_nonculture',
    'crrt_therapy',
    'patient_procedures',
    'ecmo_mcs',
    'code_status'
])
```

---

## Related Documentation

| Topic | File |
|-------|------|
| Config file structure | [configuration.md](configuration.md) |
| Table class methods | [table_classes.md](table_classes.md) |
| Utility functions | [clifpy_functions.md](clifpy_functions.md) |
| SOFA calculation code | [sofa.py](sofa.py) |
| Wide dataset code | [wide_dataset.py](wide_dataset.py) |
| Encounter stitching code | [stitching_encounters.py](stitching_encounters.py) |
