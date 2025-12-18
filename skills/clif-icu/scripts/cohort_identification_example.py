"""
Cohort Identification Example using CLIFPy
==========================================

This script demonstrates how to identify a patient cohort using CLIFPy functions.
Based on identifying CRRT patients from CLIF 2.1 standardized tables.

Author: Kaveri Chhikara
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

from clifpy.clif_orchestrator import ClifOrchestrator
from clifpy.utils.stitching_encounters import stitch_encounters

# =============================================================================
# SETUP
# =============================================================================

# Load configuration
config_path = "../config/config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

print(f"Data directory: {config['tables_path']}")
print(f"File type: {config['file_type']}")
print(f"Timezone: {config['timezone']}")

# Initialize ClifOrchestrator
clif = ClifOrchestrator(
    data_directory=config['tables_path'],
    filetype=config['file_type'],
    timezone=config['timezone']
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

print(f"Total hospitalizations: {all_encounters['hospitalization_id'].nunique():,}")

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
print(f"Adult hospitalizations (2018-2024): {len(adult_hosp_ids):,}")

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

print(f"Encounter blocks created: {encounter_mapping['encounter_block'].nunique():,}")
print(f"Original hospitalizations: {len(encounter_mapping):,}")

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
print(f"Encounter blocks with CRRT: {len(crrt_encounter_blocks):,}")

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
print(f"ESRD encounters excluded: {len(esrd_encounters):,}")
print(f"Remaining encounters: {len(final_encounter_blocks):,}")

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
print(f"Encounters with weight data: {len(encounters_with_weight):,}")
print(f"Final cohort size: {len(final_encounter_blocks):,}")

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
print(f"   Encounter blocks: {cohort_df['encounter_block'].nunique():,}")
print(f"   Hospitalizations: {cohort_df['hospitalization_id'].nunique():,}")
print(f"   Patients: {cohort_df['patient_id'].nunique():,}")

# =============================================================================
# SAVE OUTPUT
# =============================================================================

output_path = Path("../output/intermediate")
output_path.mkdir(parents=True, exist_ok=True)
cohort_df.to_parquet(output_path / "cohort_df.parquet", index=False)
print(f"\nCohort saved to: {output_path / 'cohort_df.parquet'}")
