# clifpy Utility Functions Reference

This folder contains the core utility functions from the clifpy Python library. These Python files are kept as authoritative code references for understanding clifpy's internal logic.

---

## Python Function Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| [config.py](config.py) | Configuration loading | `load_config()`, `get_config_or_params()`, `create_example_config()` |
| [io.py](io.py) | Data loading (CSV/Parquet via DuckDB) | `load_data()`, `load_parquet_with_tz()` |
| [validator.py](validator.py) | Table validation (schema, types, ranges) | `validate_dataframe()`, `validate_categorical_values()`, `check_for_duplicates()` |
| [sofa.py](sofa.py) | SOFA score calculation | `compute_sofa()`, `_impute_pao2_from_spo2()`, `_agg_extremal_values_by_id()` |
| [comorbidity.py](comorbidity.py) | CCI/Elixhauser calculation | `calculate_elix()`, `calculate_cci()` |
| [wide_dataset.py](wide_dataset.py) | Wide dataset creation | `create_wide_dataset()`, `convert_wide_to_hourly()` |
| [stitching_encounters.py](stitching_encounters.py) | Encounter stitching | `stitch_encounters()` |
| [unit_converter.py](unit_converter.py) | Medication dose unit conversion | `convert_dose_units_by_med_category()` |
| [outlier_handler.py](outlier_handler.py) | Outlier detection/removal | Handles numeric outliers based on config |
| [waterfall.py](waterfall.py) | Waterfall/cohort flow charts | Visualization of patient filtering |
| [mdro_flags.py](mdro_flags.py) | Multi-drug resistant organism flags | Identifies MDRO from culture data |
| [query.py](query.py) | DuckDB query helpers | SQL query building utilities |
| [logging_config.py](logging_config.py) | Centralized logging setup | `setup_logging()` |

---

## When to Read Each File

| Use Case | Read This File |
|----------|---------------|
| Setting up data loading configuration | [config.py](config.py) |
| Loading CSV/Parquet files with DuckDB | [io.py](io.py) |
| Understanding table validation logic | [validator.py](validator.py) |
| Computing SOFA scores | [sofa.py](sofa.py) |
| Computing CCI or Elixhauser scores | [comorbidity.py](comorbidity.py) |
| Creating wide time-series datasets | [wide_dataset.py](wide_dataset.py) |
| Stitching ED-to-inpatient encounters | [stitching_encounters.py](stitching_encounters.py) |
| Converting medication dose units | [unit_converter.py](unit_converter.py) |
| Handling outliers in numeric data | [outlier_handler.py](outlier_handler.py) |
| Creating cohort flow diagrams | [waterfall.py](waterfall.py) |
| Identifying multi-drug resistant organisms | [mdro_flags.py](mdro_flags.py) |

---

## Key Function Details

### [sofa.py](sofa.py) - SOFA Score Calculation

Computes Sequential Organ Failure Assessment (SOFA) scores from wide dataset.

**Required Categories:**
- `labs`: creatinine, platelet_count, po2_arterial, bilirubin_total
- `vitals`: map, spo2
- `patient_assessments`: gcs_total
- `medication_admin_continuous`: norepinephrine, epinephrine, dopamine, dobutamine
- `respiratory_support`: device_category, fio2_set

**Key Features:**
- Imputes PaO2 from SpO2 using Severinghaus equation when SpO2 < 97%
- Aggregates worst values per encounter for scoring
- Supports `extremal_type='worst'` for worst-case scoring

---

### [comorbidity.py](comorbidity.py) - Comorbidity Indices

Calculates comorbidity scores from ICD diagnosis codes.

**`calculate_elix(hospital_diagnosis)`**
- Elixhauser index using ICD-10-CM codes
- Quan 2011 adaptation with van Walraven weights
- Returns 31 binary condition columns + weighted score

**`calculate_cci(hospital_diagnosis)`**
- Charlson Comorbidity Index from ICD codes
- Returns weighted comorbidity score

---

### [stitching_encounters.py](stitching_encounters.py) - Encounter Stitching

Groups related hospitalizations into encounter blocks.

```python
stitch_encounters(hospitalization_df, adt_df, time_interval=6)
```

**Purpose:**
- Groups hospitalizations within time window (default 6 hours)
- Creates `encounter_block` column mapping multiple hospitalizations to single encounter
- Used when patient is discharged and readmitted quickly (ED to inpatient transfers)

**Returns:**
- `hospitalization_stitched`: Enhanced hospitalization data with encounter_block
- `adt_stitched`: Enhanced ADT data with encounter_block
- `encounter_mapping`: Mapping of hospitalization_id to encounter_block

---

### [wide_dataset.py](wide_dataset.py) - Wide Dataset Creation

Joins multiple CLIF tables into wide time-series format using DuckDB.

**Key Features:**
- Pivots narrow tables (vitals, labs) by category column
- Supports hourly aggregation with configurable methods
- High performance via DuckDB
- Category filters to select specific measurements

---

### [config.py](config.py) - Configuration Loading

Handles `clif_config.json` loading with priority:
1. If all required params provided directly → use them
2. If config_path provided → load from that path, params override
3. If no params and no config_path → auto-detect `config.json`/`config.yaml` in cwd

---

### [io.py](io.py) - Data Loading

Loads CLIF tables from CSV or Parquet files using DuckDB for efficient querying.

**Key Functions:**
- `load_data()` - Main entry point for loading any CLIF table
- `load_parquet_with_tz()` - Parquet loading with timezone handling
- Automatic ID column casting to string
- Support for filters and column selection at load time

---

### [validator.py](validator.py) - Table Validation

Comprehensive validation module for CLIF tables.

**Validation Checks:**
- Column presence and data type validation
- Castable type detection (generates warnings vs errors)
- Missing data analysis
- Categorical value validation against schema
- Duplicate checking
- Numeric range validation

---

## Related Documentation

| Topic | File |
|-------|------|
| Config file structure | [configuration.md](configuration.md) |
| Table class methods | [table_classes.md](table_classes.md) |
| ClifOrchestrator usage | [orchestrator.md](orchestrator.md) |
