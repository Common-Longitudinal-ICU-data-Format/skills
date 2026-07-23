"""
SOFA Score Calculation using CLIFpy

This script computes Sequential Organ Failure Assessment (SOFA) scores.
SOFA scores are used to track organ dysfunction in ICU patients.

The SOFA score evaluates 6 organ systems:
- Respiratory (PaO2/FiO2 ratio)
- Coagulation (platelet count)
- Liver (bilirubin)
- Cardiovascular (MAP and vasopressors)
- Central nervous system (GCS)
- Renal (creatinine)
"""

# PHI-SAFE: When an agent can see this process, run it only against non-PHI
# synthetic/demo data (see reference/phi-safe-development.md). A real-data run
# (CLIF_CONFIG_PATH set) must happen in your own secure environment with NO agent
# observing — an agent session captures stdout AND uncaught tracebacks, so print
# sanitization alone is not enough. Aggregates below are small-cell suppressed as
# defense in depth, not a license to run this where an agent can watch.

import os
import pandas as pd
import warnings
from pathlib import Path

from clifpy.clif_orchestrator import ClifOrchestrator
from clifpy.utils.sofa import REQUIRED_SOFA_CATEGORIES_BY_TABLE

warnings.filterwarnings('ignore')

# =============================================================================
# Configuration
# =============================================================================
# PHI-safe default: the non-PHI demo config written by scripts/setup_dev_data.sh.
# Override with CLIF_CONFIG_PATH for your own real run (done by you, in your secure
# environment, with the agent absent). ClifOrchestrator parses this config natively.
DEMO_CONFIG_PATH = "./clif_demo_config.json"
CONFIG_PATH = os.environ.get("CLIF_CONFIG_PATH", DEMO_CONFIG_PATH)
TIME_WINDOW_HOURS = 24  # Time window for SOFA calculation (e.g., first 24h) TODO PROJECT SPECIFIC

# Guard against an agent session silently inheriting a researcher's real-data config
# from the environment. A non-demo config requires explicit confirmation that no agent
# is observing this process (stdout AND tracebacks are captured by agent sessions).
if CONFIG_PATH != DEMO_CONFIG_PATH and os.environ.get("CLIF_ALLOW_REAL_DATA") != "1":
    raise SystemExit(
        f"Refusing to run: CLIF_CONFIG_PATH points at a non-demo config "
        f"({CONFIG_PATH!r}). If this is a real-data run, you must be in your own "
        "secure environment with NO agent observing this process. Re-run with "
        "CLIF_ALLOW_REAL_DATA=1 to confirm. See reference/phi-safe-development.md."
    )

# Small-cell suppression: never print a cohort size, record count, or distribution below
# the site threshold, since small counts can re-identify patients (reference/phi-safe-development.md).
SMALL_CELL_THRESHOLD = int(os.environ.get("CLIF_SMALL_CELL_THRESHOLD", "11"))


def safe_count(n):
    """Display a count, suppressing small cells below SMALL_CELL_THRESHOLD."""
    n = int(n)
    return f"{n:,}" if n >= SMALL_CELL_THRESHOLD else f"<suppressed (n<{SMALL_CELL_THRESHOLD})>"

# CLIF schema version this code targets. Ask the researcher which version their data
# is in before writing analysis code — 2.1 (stable) and 3.0 (multimodal) differ in
# category conventions and table set. We only DECLARE the version here (echoing it so a
# human can catch a wrong declaration — this performs NO automated version detection);
# we do NOT auto-crosswalk. The SOFA filter values below (e.g. 'creatinine',
# 'norepinephrine') follow the 2.1 convention; we do NOT convert them for 3.0, because
# blindly crosswalking would double-convert native-3.0 data and the 3.0 data dictionary
# — not this file — is the authority on which values changed. Any value renamed in 3.0
# would silently match zero rows here, so the 3.0 path warns loudly below. Migration is
# a deliberate, audited step — see the "CLIF version: 2.1 vs 3.0" section of
# reference/phi-safe-development.md.
CLIF_SCHEMA_VERSION = os.environ.get("CLIF_SCHEMA_VERSION", "2.1")
if CLIF_SCHEMA_VERSION not in ("2.1", "3.0"):
    raise SystemExit(
        f"Unsupported CLIF_SCHEMA_VERSION={CLIF_SCHEMA_VERSION!r}; expected '2.1' or '3.0'. "
        'See the "CLIF version: 2.1 vs 3.0" section of reference/phi-safe-development.md.'
    )

# =============================================================================
# Initialize ClifOrchestrator
# =============================================================================
print("=" * 60)
print("SOFA Score Calculation")
print("=" * 60)

print(f"\nTargeting CLIF schema version: {CLIF_SCHEMA_VERSION}")
if CLIF_SCHEMA_VERSION == "3.0":
    print(
        "  WARNING: this script's SOFA category filters use 2.1-convention values and are\n"
        "  NOT converted or validated for 3.0. Any category value renamed in 3.0 will\n"
        "  silently match zero rows — and because SOFA fills missing components with 0,\n"
        "  that becomes a silently understated sub-score, not an error. Reconcile the\n"
        "  filters against the 3.0 data dictionary (or migrate your data to the version\n"
        "  the filters target) before trusting these scores. See the 'CLIF version:\n"
        "  2.1 vs 3.0' section of reference/phi-safe-development.md."
    )
print("\nInitializing ClifOrchestrator...")
co = ClifOrchestrator(config_path=CONFIG_PATH)
print("✓ ClifOrchestrator initialized")

# =============================================================================
# Load Cohort Data- DEFINE YOUR COHORT- TODO
# =============================================================================
# Option 1: Load from hospitalization table (all patients)
print("\nLoading hospitalization data...")
co.load_table('hospitalization')
hosp_df = co.hospitalization.df

# Create cohort DataFrame with time windows
# Modify this section to match your cohort definition
cohort_df = pd.DataFrame({
    'hospitalization_id': hosp_df['hospitalization_id'],
    'start_time': pd.to_datetime(hosp_df['admission_dttm']),
    'end_time': pd.to_datetime(hosp_df['admission_dttm']) + pd.Timedelta(hours=TIME_WINDOW_HOURS)
})

# Option 2: If you have a specific cohort file, use this instead:
# cohort_df = pd.read_parquet('path/to/your/cohort.parquet')
# cohort_df['start_time'] = pd.to_datetime(cohort_df['your_start_column'])
# cohort_df['end_time'] = cohort_df['start_time'] + pd.Timedelta(hours=TIME_WINDOW_HOURS)

print(f"✓ Cohort prepared: {safe_count(len(cohort_df))} hospitalizations")

# Get list of hospitalization IDs for filtering
hosp_ids = cohort_df['hospitalization_id'].astype(str).unique().tolist()

# =============================================================================
# Load Required Tables for SOFA Computation
# =============================================================================
print("\nLoading tables for SOFA computation...")

# Load labs (creatinine, platelet count, PaO2, bilirubin)
co.load_table(
    'labs',
    filters={
        'hospitalization_id': hosp_ids,
        'lab_category': ['creatinine', 'platelet_count', 'po2_arterial', 'bilirubin_total']
    },
    columns=['hospitalization_id', 'lab_result_dttm', 'lab_category', 'lab_value_numeric']
)
print(f"  ✓ Labs loaded: {safe_count(len(co.labs.df))} records")

# Load vitals (MAP, SpO2, weight for dose calculations)
co.load_table(
    'vitals',
    filters={
        'hospitalization_id': hosp_ids,
        'vital_category': ['map', 'spo2', 'weight_kg', 'height_cm']
    },
    columns=['hospitalization_id', 'recorded_dttm', 'vital_category', 'vital_value']
)
print(f"  ✓ Vitals loaded: {safe_count(len(co.vitals.df))} records")

# Load patient assessments (GCS for neurological SOFA)
co.load_table(
    'patient_assessments',
    filters={
        'hospitalization_id': hosp_ids,
        'assessment_category': ['gcs_total']
    },
    columns=['hospitalization_id', 'recorded_dttm', 'assessment_category', 'numerical_value']
)
print(f"  ✓ Patient assessments loaded: {safe_count(len(co.patient_assessments.df))} records")

# Load continuous medications (vasopressors for cardiovascular SOFA)
co.load_table(
    'medication_admin_continuous',
    filters={
        'hospitalization_id': hosp_ids,
        'med_category': ['norepinephrine', 'epinephrine', 'dopamine', 'dobutamine']
    }
)
print(f"  ✓ Medications loaded: {safe_count(len(co.medication_admin_continuous.df))} records")

# Load respiratory support (for FiO2 in respiratory SOFA)
co.load_table(
    'respiratory_support',
    filters={
        'hospitalization_id': hosp_ids
    },
    columns=['hospitalization_id', 'recorded_dttm', 'device_category', 'fio2_set']
)
print(f"  ✓ Respiratory support loaded: {safe_count(len(co.respiratory_support.df))} records")

print("✓ All SOFA tables loaded")

# =============================================================================
# Clean Medication Data
# =============================================================================
print("\nCleaning medication data...")
med_df = co.medication_admin_continuous.df.copy()
initial_med_count = len(med_df)

# Remove rows with null dose values
med_df = med_df[med_df['med_dose'].notna()]
med_df = med_df[med_df['med_dose_unit'].notna()]
med_df = med_df[~med_df['med_dose_unit'].astype(str).str.lower().isin(['nan', 'none', ''])]

# Update the table
co.medication_admin_continuous.df = med_df
print(f"✓ Removed null doses: {safe_count(initial_med_count)} → {safe_count(len(med_df))} records")

# =============================================================================
# Convert Medication Units for SOFA
# =============================================================================
print("\nConverting medication units for SOFA...")

# SOFA cardiovascular scoring requires vasopressor doses in mcg/kg/min
preferred_units = {
    'norepinephrine': 'mcg/kg/min',
    'epinephrine': 'mcg/kg/min',
    'dopamine': 'mcg/kg/min',
    'dobutamine': 'mcg/kg/min'
}

co.convert_dose_units_for_continuous_meds(
    preferred_units=preferred_units,
    override=True
)
print("✓ Medication units converted")

# =============================================================================
# Filter to Successful Conversions Only
# =============================================================================
print("\nFiltering medications to successful conversions...")
med_df_converted = co.medication_admin_continuous.df_converted.copy()
converted_initial_count = len(med_df_converted)

# Keep only rows with successful conversion status
med_df_success = med_df_converted[med_df_converted['_convert_status'] == 'success'].copy()

# Update the orchestrator's converted dataframe
co.medication_admin_continuous.df_converted = med_df_success

conversion_removed_count = converted_initial_count - len(med_df_success)
print(f"✓ Filtered: {safe_count(converted_initial_count)} → {safe_count(len(med_df_success))} records")
if converted_initial_count > 0:
    # Percentage is non-identifying (a ratio, not a count); the raw removed count is suppressed.
    print(f"  Removed {safe_count(conversion_removed_count)} failed conversions ({conversion_removed_count/converted_initial_count*100:.1f}%)")

# =============================================================================
# Create Wide Dataset for SOFA
# =============================================================================
print("\nCreating wide dataset for SOFA...")

co.create_wide_dataset(
    category_filters=REQUIRED_SOFA_CATEGORIES_BY_TABLE,
    cohort_df=cohort_df,
    return_dataframe=True
)
print(f"✓ Wide dataset created: {co.wide_df.shape}")

# =============================================================================
# Add Missing Medication Columns
# =============================================================================
print("\nChecking for missing medication columns...")

required_med_cols = [
    'norepinephrine_mcg_kg_min',
    'epinephrine_mcg_kg_min',
    'dopamine_mcg_kg_min',
    'dobutamine_mcg_kg_min'
]

missing_cols = [col for col in required_med_cols if col not in co.wide_df.columns]

if missing_cols:
    for col in missing_cols:
        co.wide_df[col] = None
        print(f"  Added missing column: {col}")
    print(f"✓ Added {len(missing_cols)} missing medication columns")
else:
    print("✓ All medication columns present")

# =============================================================================
# Compute SOFA Scores
# =============================================================================
print("\nComputing SOFA scores...")

sofa_scores = co.compute_sofa_scores(
    wide_df=co.wide_df,
    id_name='hospitalization_id',
    fill_na_scores_with_zero=True,
    remove_outliers=True,
    create_new_wide_df=False
)

_n_scored = int(sofa_scores['sofa_total'].notna().sum())
print(f"\n✓ SOFA scores computed: {len(sofa_scores.columns)} columns")
if _n_scored >= SMALL_CELL_THRESHOLD:
    print(f"  Mean SOFA: {sofa_scores['sofa_total'].mean():.2f}")
    print(f"  Median SOFA: {sofa_scores['sofa_total'].median():.2f}")
    print(f"  Range: {sofa_scores['sofa_total'].min():.0f} - {sofa_scores['sofa_total'].max():.0f}")
else:
    print(f"  Aggregate SOFA stats suppressed (cohort n<{SMALL_CELL_THRESHOLD})")

# =============================================================================
# Results
# =============================================================================
print("\n" + "=" * 60)
print("SOFA Score Results")
print("=" * 60)
# PHI-safe: do NOT print per-patient rows (e.g. sofa_scores.head(10)) — on real
# data those are PHI a watching agent would see. Print columns + an aggregate score
# distribution only, and suppress the distribution (which includes the cohort count)
# when the cohort is below the small-cell threshold.
print(f"Columns: {list(sofa_scores.columns)}")
print("\nsofa_total distribution:")
if _n_scored >= SMALL_CELL_THRESHOLD:
    print(sofa_scores['sofa_total'].describe())
else:
    print(f"  Distribution suppressed (cohort n<{SMALL_CELL_THRESHOLD})")

# The sofa_scores DataFrame contains:
# - hospitalization_id
# - sofa_total (0-24)
# - Component scores: sofa_respiratory, sofa_coagulation, sofa_liver,
#                     sofa_cardiovascular, sofa_cns, sofa_renal

# =============================================================================
# Save Results (Optional)
# =============================================================================
output_path = Path('output')
output_path.mkdir(exist_ok=True)
sofa_output_file = output_path / 'sofa_scores.csv'
sofa_scores.to_csv(sofa_output_file, index=False)
print(f"\n✓ Results saved to: {sofa_output_file}")
