# clifpy Table Classes Reference

## BaseTable Inheritance Pattern

All 18 CLIF table classes inherit from `BaseTable`, providing consistent loading, validation, and analysis methods.

```python
from clifpy.tables import Vitals, Labs, PatientAssessments
# ... and 15 more table classes
```

---

## BaseTable Core Methods

| Method | Description |
|--------|-------------|
| `from_file(...)` | Class method to load data from file |
| `validate()` | Run comprehensive validation against schema |
| `isvalid()` | Check if last validation passed (bool) |
| `get_summary()` | Get table statistics as dict |
| `save_summary()` | Save summary to JSON file |
| `analyze_categorical_distributions()` | Analyze category distributions |
| `plot_categorical_distributions()` | Create bar plots for categories |
| `calculate_stratified_ecdf()` | Calculate ECDF by category |

---

## from_file() Parameters

```python
TableClass.from_file(
    data_directory=None,      # Path to data files
    filetype=None,            # "csv" or "parquet"
    timezone=None,            # Timezone string (e.g., "America/Chicago")
    config_path=None,         # Path to config file (alternative to above)
    output_directory=None,    # Where to save outputs
    sample_size=None,         # Limit rows loaded (int)
    columns=None,             # List of specific columns to load
    filters=None,             # Dict of filters to apply
    verbose=False             # Show loading messages
)
```

### Loading Examples

```python
from clifpy.tables import Vitals, Labs

# Load all vitals
vitals = Vitals.from_file(
    data_directory="/path/to/data",
    filetype="parquet",
    timezone="America/Chicago"
)

# Load specific vital categories for specific hospitalizations
vitals = Vitals.from_file(
    config_path="clif_config.json",
    filters={
        'hospitalization_id': ['H001', 'H002', 'H003'],
        'vital_category': ['heart_rate', 'sbp', 'spo2']
    }
)

# Load sample for testing
labs = Labs.from_file(
    config_path="clif_config.json",
    sample_size=1000
)
```

---

## Table-Specific Methods

### Vitals

```python
vitals = Vitals.from_file(config_path="config.json")

# Filter by vital type
hr_df = vitals.filter_by_vital_category('heart_rate')

# Get summary statistics per vital category
stats = vitals.get_vital_summary_stats()

# Access vital ranges from schema
ranges = vitals.vital_ranges  # {'heart_rate': {'min': 20, 'max': 300}, ...}
units = vitals.vital_units    # {'heart_rate': 'bpm', 'temp_c': 'C', ...}
```

### Labs

```python
labs = Labs.from_file(config_path="config.json")

# Get unique reference units in data
units_df = labs.get_lab_reference_units(save=True)

# Standardize unit strings to match schema
labs.standardize_reference_units(inplace=True, lowercase=False)

# Get summary statistics per lab category
stats = labs.get_lab_category_stats()
```

---

## Available Table Classes

| Class | Table Name | Category Column(s) |
|-------|------------|-------------------|
| `Vitals` | vitals | `vital_category` |
| `Labs` | labs | `lab_category` |
| `PatientAssessments` | patient_assessments | `assessment_category` |
| `MedicationAdminContinuous` | medication_admin_continuous | `med_category`, `action_category` |
| `MedicationAdminIntermittent` | medication_admin_intermittent | `med_category`, `action_category` |
| `RespiratorySupport` | respiratory_support | `device_category`, `mode_category` |
| `MicrobiologyCulture` | microbiology_culture | `organism_category`, `fluid_category` |
| `Patient` | patient | `sex_category`, `race_category`, `ethnicity_category` |
| `Hospitalization` | hospitalization | `admission_type_category`, `discharge_category` |
| `Adt` | adt | `location_category`, `location_type` |
| `CodeStatus` | code_status | `code_status_category` |
| `Position` | position | `position_category` |
| `CrrtTherapy` | crrt_therapy | `crrt_mode_category` |
| `EcmoMcs` | ecmo_mcs | `device_category` |
| `HospitalDiagnosis` | hospital_diagnosis | (uses ICD codes, not categories) |
| `PatientProcedures` | patient_procedures | (uses CPT/ICD10PCS codes) |
| `MicrobiologySusceptibility` | microbiology_susceptibility | `susceptibility_category` |
| `MicrobiologyNonculture` | microbiology_nonculture | `result_category` |

---

## Validation

Each table validates against its YAML schema:

```python
# Run validation
vitals.validate()

# Check if valid
if vitals.isvalid():
    print("Data passes all validation checks")
else:
    print(f"Found {len(vitals.errors)} errors")
    for error in vitals.errors:
        print(error)
```

### Validation Checks

- Required columns present
- Data types match schema
- Categorical values in permissible set
- Composite key uniqueness
- Datetime timezone validation
- Numeric range validation (outliers)
- Missing data statistics

---

## Accessing Data

After loading, access the DataFrame:

```python
vitals = Vitals.from_file(config_path="config.json")

# Access the DataFrame
df = vitals.df

# Access table metadata
print(vitals.table_name)       # 'vitals'
print(vitals.data_directory)   # '/path/to/data'
print(vitals.timezone)         # 'America/Chicago'
print(vitals.schema)           # Schema dict from YAML
```

---

## Related Documentation

| Topic | File |
|-------|------|
| Config file structure | [configuration.md](configuration.md) |
| ClifOrchestrator usage | [orchestrator.md](orchestrator.md) |
| Utility functions | [clifpy_functions.md](clifpy_functions.md) |
| Validation code | [validator.py](validator.py) |
