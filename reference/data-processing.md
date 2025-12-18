# Data Processing Utilities

## Create Wide Dataset

Convert long-format CLIF tables to wide format for analysis.

**Requires ClifOrchestrator.**

```python
from clifpy import ClifOrchestrator
from clifpy.utils import create_wide_dataset

co = ClifOrchestrator(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern'
)

wide_df = create_wide_dataset(
    clif_instance=co,
    category_filters={
        'vitals': ['heart_rate', 'sbp', 'spo2', 'temp_c'],
        'labs': ['hemoglobin', 'creatinine', 'lactate', 'wbc']
    },
    hospitalization_ids=hosp_ids,  # Filter by IDs
    output_format='dataframe'       # or 'csv', 'parquet'
)
```

---

## Convert to Hourly Aggregation

Aggregate wide dataset into hourly windows.

```python
from clifpy.utils import convert_wide_to_hourly

hourly_df = convert_wide_to_hourly(
    wide_df,
    aggregation_config={
        'max': ['heart_rate', 'temp_c'],
        'min': ['sbp', 'spo2'],
        'mean': ['hemoglobin'],
        'last': ['creatinine'],
        'boolean': ['norepinephrine'],      # Any non-null = True
        'one_hot_encode': ['device_category']
    },
    id_name='hospitalization_id',
    hourly_window=1,              # 1-72 hours
    fill_gaps=True                # Create rows for empty windows
)
```

**Aggregation Methods:**
- `max`, `min`, `mean`, `median` - Numeric aggregation
- `first`, `last` - First/last value in window
- `boolean` - Any non-null value = True
- `one_hot_encode` - Create binary columns for each category value

---

## Stitch Encounters

Link related hospitalizations within a time window.

```python
from clifpy.tables import Hospitalization, Adt
from clifpy.utils import stitch_encounters

hosp = Hospitalization.from_file(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern',
    filters={'hospitalization_id': hosp_ids}
)

adt = Adt.from_file(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern',
    filters={'hospitalization_id': hosp_ids}
)

hosp_stitched, adt_stitched, mapping = stitch_encounters(
    hospitalization=hosp.df,
    adt=adt.df,
    time_interval=6  # Hours between encounters
)
```

**Returns tuple of 3 DataFrames:**
1. `hosp_stitched` - Hospitalization with `encounter_block` column
2. `adt_stitched` - ADT with `encounter_block` column
3. `mapping` - hospitalization_id to encounter_block mapping

---

## Respiratory Support Waterfall

Forward-fill respiratory support data within device/mode blocks.

```python
from clifpy.tables import RespiratorySupport

resp = RespiratorySupport.from_file(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern',
    filters={'hospitalization_id': hosp_ids}
)

resp_filled = resp.waterfall(
    bfill=False,    # Forward-fill only (True for bidirectional)
    verbose=True
)

cleaned_df = resp_filled.df
```

**Processing:**
- Creates hourly scaffold
- Infers device/mode from context
- Forward-fills FiO2, PEEP, tidal volume within mode blocks
- Scales FiO2 if needed (40 → 0.40)

---

## Outlier Handling

Detect and remove outliers based on clinical ranges.

```python
from clifpy.utils import apply_outlier_handling, get_outlier_summary

# Get summary without modifying
summary = get_outlier_summary(table)

# Apply outlier handling (modifies in-place, sets outliers to NaN)
apply_outlier_handling(table)
```

**Handles:**
- Simple ranges (min/max per category)
- Category-dependent ranges (vitals, labs)
- Medication dose ranges with unit-dependent logic

---

## Unit Conversion (Medications)

Standardize medication dose units.

```python
from clifpy.utils.unit_converter import standardize_dose_to_base_units

converted_df, counts = standardize_dose_to_base_units(
    med_df,
    vitals_df=vitals_df  # For weight-based dosing (/kg, /lb)
)
```

**Converts to base units:**
- mcg/min (mass rate)
- ml/min (volume rate)
- u/min (units rate)

**Handles:**
- Weight-based: /kg → /min using patient weight
- Time conversions: /hr → /min
- Mass conversions: mg → mcg, g → mg
