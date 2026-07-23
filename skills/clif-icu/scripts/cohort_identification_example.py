"""
Cohort Identification Example using CLIFPy
==========================================

This script demonstrates how to identify a patient cohort using CLIFPy functions.
Based on identifying CRRT patients from CLIF 2.1 standardized tables.

Author: Kaveri Chhikara
"""

# PHI-SAFE: When an agent can see this process, run it only against non-PHI
# synthetic/demo data (see reference/phi-safe-development.md). A real-data run
# (CLIF_CONFIG_PATH set) must happen in your own secure environment with NO agent
# observing — an agent session captures stdout AND uncaught tracebacks, so print
# sanitization alone is not enough. Counts below are small-cell suppressed as
# defense in depth, not a license to run this where an agent can watch.

import os
import pandas as pd
import numpy as np
import json
from pathlib import Path

from clifpy.clif_orchestrator import ClifOrchestrator
from clifpy.utils.stitching_encounters import stitch_encounters

# =============================================================================
# SETUP
# =============================================================================

# PHI-safe default: point at the non-PHI demo config written by
# scripts/setup_dev_data.sh. Override with CLIF_CONFIG_PATH for your own real run
# (which you do yourself, in your secure environment, with no agent watching).
DEMO_CONFIG_PATH = "./clif_demo_config.json"
config_path = os.environ.get("CLIF_CONFIG_PATH", DEMO_CONFIG_PATH)

# Guard against an agent session silently inheriting a researcher's real-data
# config from the environment. A non-demo config requires explicit confirmation
# that no agent is observing this process (stdout AND tracebacks are captured).
if config_path != DEMO_CONFIG_PATH and os.environ.get("CLIF_ALLOW_REAL_DATA") != "1":
    raise SystemExit(
        f"Refusing to run: CLIF_CONFIG_PATH points at a non-demo config "
        f"({config_path!r}). If this is a real-data run, you must be in your own "
        "secure environment with NO agent observing this process. Re-run with "
        "CLIF_ALLOW_REAL_DATA=1 to confirm. See reference/phi-safe-development.md."
    )

# Small-cell suppression: never print a count below the site threshold, since small
# cohort/subgroup sizes can re-identify patients (see reference/phi-safe-development.md).
SMALL_CELL_THRESHOLD = int(os.environ.get("CLIF_SMALL_CELL_THRESHOLD", "11"))


def safe_count(n):
    """Display a count, suppressing small cells below SMALL_CELL_THRESHOLD."""
    n = int(n)
    return f"{n:,}" if n >= SMALL_CELL_THRESHOLD else f"<suppressed (n<{SMALL_CELL_THRESHOLD})>"


# CLIF schema version this code targets. Ask the researcher which version their data
# is in before writing analysis code — 2.1 (stable) and 3.0 (multimodal) differ in
# category conventions and table set. We only DECLARE the version here (echoing it so a
# human can catch a wrong declaration — this performs NO automated version detection);
# we do NOT auto-crosswalk. This example's category values follow the 2.1 convention and
# are NOT converted for 3.0, so any value renamed in 3.0 would silently match zero rows;
# the 3.0 path warns about this below. Migration 2.1 -> 3.0 is a deliberate, audited step
# — see the "CLIF version: 2.1 vs 3.0" section of reference/phi-safe-development.md.
CLIF_SCHEMA_VERSION = os.environ.get("CLIF_SCHEMA_VERSION", "2.1")
if CLIF_SCHEMA_VERSION not in ("2.1", "3.0"):
    raise SystemExit(
        f"Unsupported CLIF_SCHEMA_VERSION={CLIF_SCHEMA_VERSION!r}; expected '2.1' or '3.0'. "
        'See the "CLIF version: 2.1 vs 3.0" section of reference/phi-safe-development.md.'
    )


with open(config_path, 'r') as f:
    config = json.load(f)

# Accept both key variants: create_example_config writes data_directory/filetype;
# some hand-written YAML-style configs use tables_path/file_type.
data_directory = config.get("data_directory") or config["tables_path"]
filetype = config.get("filetype") or config["file_type"]
timezone = config["timezone"]

# Do NOT print the data directory path or any row values — on real data those can
# reveal PHI to a watching agent. Print only non-identifying settings.
print(f"Targeting CLIF schema version: {CLIF_SCHEMA_VERSION}")
if CLIF_SCHEMA_VERSION == "3.0":
    print(
        "  WARNING: this example's category values follow the 2.1 convention and are NOT\n"
        "  converted or validated for 3.0. Any value renamed in 3.0 will silently match\n"
        "  zero rows, quietly shrinking the cohort. Reconcile the filters against the 3.0\n"
        "  data dictionary (or migrate your data first). See the 'CLIF version: 2.1 vs\n"
        "  3.0' section of reference/phi-safe-development.md."
    )
print(f"File type: {filetype}")
print(f"Timezone: {timezone}")

# Initialize ClifOrchestrator
clif = ClifOrchestrator(
    data_directory=data_directory,
    filetype=filetype,
    timezone=timezone
)

# =============================================================================
# STEP 0: LOAD CORE TABLES
# =============================================================================

print("\n" + "=" * 60)
print("Step 0: Loading Core Tables")
print("=" * 60)

clif.load_table('patient')
clif.load_table('hospitalization')
clif.load_table('adt')

print(f"Patient: {len(clif.patient.df):,} rows")
print(f"Hospitalization: {len(clif.hospitalization.df):,} rows")
print(f"ADT: {len(clif.adt.df):,} rows")

# =============================================================================
# STEP 1: FILTER BY AGE AND DATE
# =============================================================================

print("\n" + "=" * 60)
print("Step 1: Filter Adults (age >= 18) and Admissions 2018-2024")
print("=" * 60)

hosp_df = clif.hospitalization.df
adt_df = clif.adt.df

# Merge hospitalization and ADT
all_encounters = pd.merge(
    hosp_df[["patient_id", "hospitalization_id", "admission_dttm", "discharge_dttm", 
             "age_at_admission", "discharge_category"]],
    adt_df[["hospitalization_id", "hospital_id", "in_dttm", "out_dttm", 
            "location_category", "location_type"]],
    on='hospitalization_id',
    how='inner'
)

print(f"Total hospitalizations: {safe_count(all_encounters['hospitalization_id'].nunique())}")

# Filter for adults
adult_encounters = all_encounters[
    (all_encounters['age_at_admission'] >= 18) & 
    (all_encounters['age_at_admission'].notna())
].copy()

# Filter for study period
adult_encounters = adult_encounters[
    (adult_encounters['admission_dttm'].dt.year >= 2018) & 
    (adult_encounters['admission_dttm'].dt.year <= 2024)
]

adult_hosp_ids = set(adult_encounters['hospitalization_id'].unique())
print(f"Adult hospitalizations (2018-2024): {safe_count(len(adult_hosp_ids))}")

# =============================================================================
# STEP 2: STITCH ENCOUNTERS
# =============================================================================

print("\n" + "=" * 60)
print("Step 2: Stitch Encounters (6-hour window)")
print("=" * 60)

# Filter to adult hospitalizations
hosp_filtered = clif.hospitalization.df[clif.hospitalization.df['hospitalization_id'].isin(adult_hosp_ids)]
adt_filtered = clif.adt.df[clif.adt.df['hospitalization_id'].isin(adult_hosp_ids)]

# Stitch encounters
hosp_stitched, adt_stitched, encounter_mapping = stitch_encounters(
    hospitalization=hosp_filtered,
    adt=adt_filtered,
    time_interval=6
)

# Update orchestrator
clif.hospitalization.df = hosp_stitched
clif.adt.df = adt_stitched
clif.encounter_mapping = encounter_mapping

print(f"Encounter blocks created: {safe_count(encounter_mapping['encounter_block'].nunique())}")
print(f"Original hospitalizations: {safe_count(len(encounter_mapping))}")

# =============================================================================
# STEP 3: IDENTIFY CRRT ENCOUNTERS
# =============================================================================

print("\n" + "=" * 60)
print("Step 3: Identify CRRT Encounters")
print("=" * 60)

clif.load_table('crrt_therapy')
print(f"CRRT therapy loaded: {len(clif.crrt_therapy.df):,} rows")

# Merge with encounter mapping
clif.crrt_therapy.df = clif.crrt_therapy.df.merge(
    clif.encounter_mapping[['hospitalization_id', 'encounter_block']],
    on='hospitalization_id',
    how='left'
)

crrt_encounter_blocks = set(clif.crrt_therapy.df['encounter_block'].dropna().unique())
print(f"Encounter blocks with CRRT: {safe_count(len(crrt_encounter_blocks))}")

# =============================================================================
# STEP 4: EXCLUDE ESRD
# =============================================================================

print("\n" + "=" * 60)
print("Step 4: Exclude ESRD (present on admission)")
print("=" * 60)

clif.load_table('hospital_diagnosis')
print(f"Diagnoses loaded: {len(clif.hospital_diagnosis.df):,} rows")

# Merge with encounter mapping
clif.hospital_diagnosis.df = clif.hospital_diagnosis.df.merge(
    clif.encounter_mapping[['hospitalization_id', 'encounter_block']],
    on='hospitalization_id',
    how='left'
)

# Filter to CRRT encounters, present on admission
diagnosis_df = clif.hospital_diagnosis.df[
    (clif.hospital_diagnosis.df['encounter_block'].isin(crrt_encounter_blocks)) &
    (clif.hospital_diagnosis.df['present_on_admission'] == True)
]

# ESRD ICD codes
esrd_codes = ['N185', 'N186', 'Z992']
esrd_mask = diagnosis_df['diagnosis_code'].apply(
    lambda x: any(str(x).startswith(code) for code in esrd_codes)
)
esrd_encounters = set(diagnosis_df.loc[esrd_mask, 'encounter_block'].unique())

final_encounter_blocks = crrt_encounter_blocks - esrd_encounters
print(f"ESRD encounters excluded: {safe_count(len(esrd_encounters))}")
print(f"Remaining encounters: {safe_count(len(final_encounter_blocks))}")

# =============================================================================
# STEP 5: CHECK WEIGHT AVAILABILITY
# =============================================================================

print("\n" + "=" * 60)
print("Step 5: Check Weight Data Availability")
print("=" * 60)

clif.load_table(
    'vitals',
    columns=['hospitalization_id', 'recorded_dttm', 'vital_category', 'vital_value'],
    categories=['weight_kg']
)
print(f"Vitals (weight) loaded: {len(clif.vitals.df):,} rows")

# Merge with encounter mapping
clif.vitals.df = clif.vitals.df.merge(
    clif.encounter_mapping[['hospitalization_id', 'encounter_block']],
    on='hospitalization_id',
    how='left'
)

# Filter to cohort
weight_df = clif.vitals.df[clif.vitals.df['encounter_block'].isin(final_encounter_blocks)]
encounters_with_weight = set(weight_df['encounter_block'].unique())

final_encounter_blocks = final_encounter_blocks & encounters_with_weight
print(f"Encounters with weight data: {safe_count(len(encounters_with_weight))}")
print(f"Final cohort size: {safe_count(len(final_encounter_blocks))}")

# =============================================================================
# STEP 6: BUILD FINAL COHORT
# =============================================================================

print("\n" + "=" * 60)
print("Step 6: Build Final Cohort DataFrame")
print("=" * 60)

# Filter encounter mapping to final cohort
cohort_df = encounter_mapping[
    encounter_mapping['encounter_block'].isin(final_encounter_blocks)
].copy()

# Add patient demographics
patient_df = clif.patient.df[['patient_id', 'death_dttm', 'race_category', 'sex_category', 'ethnicity_category']]
hosp_df = clif.hospitalization.df[
    ['hospitalization_id', 'patient_id', 'admission_dttm', 'discharge_dttm', 
     'age_at_admission', 'discharge_category']
]

cohort_df = cohort_df.merge(hosp_df, on='hospitalization_id', how='left')
cohort_df = cohort_df.merge(patient_df, on='patient_id', how='left')

print(f"\nFinal Cohort:")
print(f"   Encounter blocks: {safe_count(cohort_df['encounter_block'].nunique())}")
print(f"   Hospitalizations: {safe_count(cohort_df['hospitalization_id'].nunique())}")
print(f"   Patients: {safe_count(cohort_df['patient_id'].nunique())}")

# =============================================================================
# SAVE OUTPUT
# =============================================================================

output_path = Path("../output/intermediate")
output_path.mkdir(parents=True, exist_ok=True)
cohort_df.to_parquet(output_path / "cohort_df.parquet", index=False)
print(f"\nCohort saved to: {output_path / 'cohort_df.parquet'}")
