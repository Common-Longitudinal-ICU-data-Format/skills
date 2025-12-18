# Clinical Score Calculations

## SOFA Score

Sequential Organ Failure Assessment score (0-24).

```python
from clifpy.utils import compute_sofa

sofa_df = compute_sofa(
    wide_df,                          # Wide dataset with SOFA variables
    id_name='hospitalization_id',     # or 'encounter_block'
    fill_na_scores_with_zero=True     # Fill missing component scores with 0
)
```

**Returns DataFrame with:**
- `sofa_cv` - Cardiovascular (0-4)
- `sofa_coag` - Coagulation (0-4)
- `sofa_liver` - Liver (0-4)
- `sofa_resp` - Respiratory (0-4)
- `sofa_cns` - Central Nervous System (0-4)
- `sofa_renal` - Renal (0-4)
- `sofa_total` - Total score (0-24)

**Required Variables in wide_df:**
- Cardiovascular: MAP, vasopressor doses (norepinephrine, epinephrine, dopamine, dobutamine)
- Coagulation: Platelets
- Liver: Bilirubin
- Respiratory: PaO2/FiO2 ratio (or SpO2-derived)
- CNS: GCS total
- Renal: Creatinine, urine output

---

## Charlson Comorbidity Index (CCI)

```python
from clifpy.tables import HospitalDiagnosis
from clifpy.utils import calculate_cci

dx = HospitalDiagnosis.from_file(
    data_directory='/path/to/data',
    filetype='parquet',
    timezone='US/Eastern',
    filters={'hospitalization_id': hosp_ids}
)

cci_df = calculate_cci(
    dx,                    # HospitalDiagnosis table or DataFrame
    hierarchy=True         # Prevent double-counting mild/severe forms
)
```

**Returns DataFrame with 17 condition columns + `cci_score`:**

| Condition | Weight |
|-----------|--------|
| myocardial_infarction | 1 |
| congestive_heart_failure | 1 |
| peripheral_vascular_disease | 1 |
| cerebrovascular_disease | 1 |
| dementia | 1 |
| chronic_pulmonary_disease | 1 |
| rheumatic_disease | 1 |
| peptic_ulcer_disease | 1 |
| mild_liver_disease | 1 |
| diabetes_without_complications | 1 |
| diabetes_with_complications | 2 |
| hemiplegia_paraplegia | 2 |
| renal_disease | 2 |
| malignancy | 2 |
| moderate_severe_liver_disease | 3 |
| metastatic_solid_tumor | 6 |
| aids_hiv | 6 |

---

## Elixhauser Comorbidity Index

```python
from clifpy.utils import calculate_elix

elix_df = calculate_elix(
    dx,                    # HospitalDiagnosis table or DataFrame
    hierarchy=True         # Prevent double-counting
)
```

**Returns DataFrame with 31 condition columns + `elix_score`:**

Conditions include: congestive_heart_failure, cardiac_arrhythmias, valvular_disease, pulmonary_circulation_disorders, peripheral_vascular_disorders, hypertension_uncomplicated, hypertension_complicated, paralysis, other_neurological_disorders, chronic_pulmonary_disease, diabetes_uncomplicated, diabetes_complicated, hypothyroidism, renal_failure, liver_disease, peptic_ulcer_disease, aids_hiv, lymphoma, metastatic_cancer, solid_tumor, rheumatoid_arthritis, coagulopathy, obesity, weight_loss, fluid_electrolyte_disorders, blood_loss_anemia, deficiency_anemia, alcohol_abuse, drug_abuse, psychoses, depression

---

## MDRO Flags

Multi-Drug Resistant Organism detection.

```python
from clifpy.tables import MicrobiologyCulture, MicrobiologySusceptibility
from clifpy.utils import calculate_mdro_flags

culture = MicrobiologyCulture.from_file(...)
susceptibility = MicrobiologySusceptibility.from_file(...)

mdro_df = calculate_mdro_flags(
    culture=culture,
    susceptibility=susceptibility,
    organism_name='pseudomonas_aeruginosa',  # Target organism
    hospitalization_ids=hosp_ids             # Optional filter
)
```

**Returns DataFrame with:**
- Individual antimicrobial columns (e.g., `amikacin_agent`)
- Group resistance flags (e.g., `aminoglycosides_group`)
- MDRO flags:
  - `mdr` - Multi-Drug Resistant
  - `xdr` - Extensively Drug Resistant
  - `pdr` - Pan-Drug Resistant
  - `dtr` - Difficult-to-Treat Resistant

**Supported Organisms:**
- pseudomonas_aeruginosa
- acinetobacter_baumannii
- enterobacterales (E. coli, Klebsiella, etc.)
- staphylococcus_aureus
- enterococcus species
