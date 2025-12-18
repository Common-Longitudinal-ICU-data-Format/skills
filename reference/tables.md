# CLIF Tables Reference

Complete reference for all 20 CLIF tables with schema links and available categories.

---

## Long Tables (Filter by Category)

These tables have many rows per hospitalization. **Always filter by both hospitalization_id AND category.**

### vitals
| Property | Value |
|----------|-------|
| **Class** | `Vitals` |
| **Schema** | [mCIDE/vitals/](../mCIDE/vitals/clif_vitals_categories.csv) |
| **Category Column** | `vital_category` |
| **Categories** | temp_c, heart_rate, sbp, dbp, spo2, respiratory_rate, map, height_cm, weight_kg |

```python
from clifpy.tables import Vitals
vitals = Vitals.from_file(
    data_directory='/path/to/data', filetype='parquet', timezone='US/Eastern',
    filters={'hospitalization_id': ids, 'vital_category': ['heart_rate', 'sbp', 'spo2']}
)
```

---

### labs
| Property | Value |
|----------|-------|
| **Class** | `Labs` |
| **Schema** | [mCIDE/labs/](../mCIDE/labs/clif_lab_categories.csv) |
| **Category Column** | `lab_category` |
| **Count** | 53 categories |
| **Order Groups** | blood_gas, bmp, cbc, coags, lft, misc |

**Common Categories:**
- **CBC:** hemoglobin, hematocrit, wbc, platelets, mch, mchc, mcv, rdw
- **BMP:** sodium, potassium, chloride, bicarbonate, bun, creatinine, glucose_serum, calcium
- **LFT:** alt, ast, alkaline_phosphatase, bilirubin_total, bilirubin_direct, albumin
- **Coags:** inr, pt, ptt, fibrinogen, d_dimer
- **Blood Gas:** pao2, paco2, ph_arterial, ph_venous, base_excess
- **Misc:** lactate, troponin_i, troponin_t, bnp, procalcitonin, crp, magnesium, phosphorus

```python
from clifpy.tables import Labs
labs = Labs.from_file(
    data_directory='/path/to/data', filetype='parquet', timezone='US/Eastern',
    filters={'hospitalization_id': ids, 'lab_category': ['hemoglobin', 'creatinine', 'lactate']}
)
```

---

### patient_assessments
| Property | Value |
|----------|-------|
| **Class** | `PatientAssessments` |
| **Schema** | [mCIDE/patient_assessments/](../mCIDE/patient_assessments/clif_patient_assessment_categories.csv) |
| **Category Column** | `assessment_category` |
| **Count** | 72 categories |

**By Group:**
- **Neurological:** gcs_total, gcs_eye, gcs_motor, gcs_verbal, AVPU, APGAR
- **Sedation/Agitation:** RASS, SAS
- **Delirium:** cam_icu, cam_icu_features, ICSDC
- **Pain:** BPS, cpot_total, DVPRS, NRS, VAS, PAINAD
- **Mobility:** AM-PAC, AMS, IMS
- **Nursing Risk:** braden_total, braden_sensory, braden_moisture, Morse_Fall_Scale
- **Withdrawal:** CIWA, COWS, WAT, MINDS
- **SAT/SBT:** sat_screen, sat_delivery, sbt_screen, sbt_delivery

```python
from clifpy.tables import PatientAssessments
assessments = PatientAssessments.from_file(
    data_directory='/path/to/data', filetype='parquet', timezone='US/Eastern',
    filters={'hospitalization_id': ids, 'assessment_category': ['gcs_total', 'rass', 'cam_icu']}
)
```

---

### medication_admin_continuous
| Property | Value |
|----------|-------|
| **Class** | `MedicationAdminContinuous` |
| **Schema** | [mCIDE/medication_admin_continuous/](../mCIDE/medication_admin_continuous/clif_medication_admin_continuous_med_categories.csv) |
| **Category Column** | `med_category` |
| **Count** | 78 medications |
| **Action Column** | `action_category`: start, stop, going, dose_change |

**By Group:**
- **Vasoactives:** norepinephrine, epinephrine, dopamine, vasopressin, phenylephrine, angiotensin_ii
- **Cardiac:** dobutamine, milrinone, isoproterenol, amiodarone, diltiazem, esmolol, nicardipine, nitroglycerin, nitroprusside
- **Sedation:** propofol, fentanyl, midazolam, dexmedetomidine, ketamine, lorazepam, morphine, hydromorphone
- **Paralytics:** cisatracurium, rocuronium, vecuronium
- **Anticoagulation:** heparin, bivalirudin, argatroban
- **Diuretics:** furosemide, bumetanide
- **Pulmonary Vasodilators:** epoprostenol, nitric_oxide, treprostinil
- **Fluids:** albumin, lactated_ringers, plasmalyte, sodium_bicarbonate, tpn
- **Endocrine:** insulin, oxytocin

```python
from clifpy.tables import MedicationAdminContinuous
meds = MedicationAdminContinuous.from_file(
    data_directory='/path/to/data', filetype='parquet', timezone='US/Eastern',
    filters={'hospitalization_id': ids, 'med_category': ['norepinephrine', 'propofol', 'fentanyl']}
)
```

---

### medication_admin_intermittent
| Property | Value |
|----------|-------|
| **Class** | `MedicationAdminIntermittent` |
| **Schema** | [mCIDE/medication_admin_intermittent/](../mCIDE/medication_admin_intermittent/clif_medication_admin_intermittent_med_categories.csv) |
| **Category Column** | `med_category` |
| **Count** | 100+ medications |
| **Action Column** | `action_category`: given, not_given, bolus, other |

**Common Categories:** vancomycin, cefepime, piperacillin_tazobactam, meropenem, ceftriaxone, azithromycin, metronidazole, fluconazole, acyclovir, oseltamivir

```python
from clifpy.tables import MedicationAdminIntermittent
meds = MedicationAdminIntermittent.from_file(
    data_directory='/path/to/data', filetype='parquet', timezone='US/Eastern',
    filters={'hospitalization_id': ids, 'med_category': ['vancomycin', 'cefepime']}
)
```

---

### respiratory_support
| Property | Value |
|----------|-------|
| **Class** | `RespiratorySupport` |
| **Schema** | [mCIDE/respiratory_support/](../mCIDE/respiratory_support/) |
| **Device Column** | `device_category` |
| **Mode Column** | `mode_category` |

**Devices:** IMV, NIPPV, CPAP, High_Flow_NC, Face_Mask, Trach_Collar, Nasal_Cannula, Room_Air, Other

**Modes:** Assist_Control_Volume_Control, Pressure_Control, PRVC, SIMV, Pressure_Support_CPAP, Volume_Support, Blow_by, Other

```python
from clifpy.tables import RespiratorySupport
resp = RespiratorySupport.from_file(
    data_directory='/path/to/data', filetype='parquet', timezone='US/Eastern',
    filters={'hospitalization_id': ids, 'device_category': ['IMV', 'NIPPV', 'High_Flow_NC']}
)
```

---

### microbiology_culture
| Property | Value |
|----------|-------|
| **Class** | `MicrobiologyCulture` |
| **Schema** | [mCIDE/microbiology_culture/](../mCIDE/microbiology_culture/) |
| **Organism Column** | `organism_category` |
| **Fluid Column** | `fluid_category` |
| **Count** | 545+ organisms |

**Common Organisms:** staphylococcus_aureus, escherichia_coli, klebsiella_pneumoniae, pseudomonas_aeruginosa, enterococcus_faecalis, candida_albicans, no_growth

```python
from clifpy.tables import MicrobiologyCulture
cultures = MicrobiologyCulture.from_file(
    data_directory='/path/to/data', filetype='parquet', timezone='US/Eastern',
    filters={'hospitalization_id': ids}
)
```

---

## Demographic/Status Tables

These have fewer rows per hospitalization. Filter by hospitalization_id only.

### patient
| Property | Value |
|----------|-------|
| **Class** | `Patient` |
| **Schema** | [mCIDE/patient/](../mCIDE/patient/) |

| Category Column | Values |
|-----------------|--------|
| sex_category | Male, Female, Unknown |
| race_category | White, Black_or_African_American, Asian, American_Indian_or_Alaska_Native, Native_Hawaiian_or_Pacific_Islander, Unknown, Other |
| ethnicity_category | Hispanic_or_Latino, Non_Hispanic_or_Latino, Unknown |
| language_category | 150+ languages |

---

### hospitalization
| Property | Value |
|----------|-------|
| **Class** | `Hospitalization` |
| **Schema** | [mCIDE/hospitalization/](../mCIDE/hospitalization/) |

| Category Column | Values |
|-----------------|--------|
| admission_type_category | ed, facility, osh, direct, elective, other |
| discharge_category | Home, SNF, Expired, Hospice, LTACH, Acute_Care_Hospital, AMA, Psychiatric_Hospital, Jail, Shelter, Still_Admitted, Missing, Other (17 total) |

---

### adt
| Property | Value |
|----------|-------|
| **Class** | `Adt` |
| **Schema** | [mCIDE/adt/](../mCIDE/adt/) |

| Category Column | Values |
|-----------------|--------|
| location_category | ed, ward, stepdown, icu, procedural, l&d, hospice, psych, rehab, radiology, dialysis, other |
| location_type | general_icu, cardiac_icu, surgical_icu, medical_icu, neuro_icu, burn_icu, mixed_* |
| hospital_type | academic, community, LTACH |

---

### code_status
| Property | Value |
|----------|-------|
| **Class** | `CodeStatus` |
| **Schema** | [mCIDE/code_status/](../mCIDE/code_status/clif_code_status_categories.csv) |
| **Category Column** | `code_status_category` |
| **Values** | DNR, DNAR, UDNR, DNR/DNI, DNAR/DNI, DNI_only, AND, Full, Presume_Full, Other |

---

### position
| Property | Value |
|----------|-------|
| **Class** | `Position` |
| **Schema** | [mCIDE/postion/](../mCIDE/postion/clif_position_categories.csv) |
| **Category Column** | `position_category` |
| **Values** | prone, not_prone |

---

### crrt_therapy
| Property | Value |
|----------|-------|
| **Class** | `CrrtTherapy` |
| **Schema** | [mCIDE/crrt_therapy/](../mCIDE/crrt_therapy/clif_crrt_therapy_mode_categories.csv) |
| **Category Column** | `crrt_mode_category` |
| **Values** | scuf, cvvh, cvvhd, cvvhdf, avvh |

---

### ecmo_mcs
| Property | Value |
|----------|-------|
| **Class** | `EcmoMcs` |
| **Schema** | mCIDE/ecmo/ |
| **Category Column** | `device_category` |

---

## Code-Based Tables

These use ICD/CPT codes, not standardized categories.

### hospital_diagnosis
| Property | Value |
|----------|-------|
| **Class** | `HospitalDiagnosis` |
| **Key Columns** | diagnosis_code, diagnosis_primary, poa_present |
| **Note** | ICD-9/ICD-10 codes, use for CCI/Elixhauser calculation |

---

### patient_procedures
| Property | Value |
|----------|-------|
| **Class** | `PatientProcedures` |
| **Key Columns** | procedure_code |
| **Note** | CPT, ICD10PCS, HCPCS codes |

---

### microbiology_susceptibility
| Property | Value |
|----------|-------|
| **Class** | `MicrobiologySusceptibility` |
| **Schema** | [mCIDE/microbiology_susceptibility/](../mCIDE/microbiology_susceptibility/) |
| **Category Column** | `susceptibility_category` |
| **Values** | susceptible, non_susceptible, indeterminate, NA |

---

### microbiology_nonculture
| Property | Value |
|----------|-------|
| **Class** | `MicrobiologyNonculture` |
| **Schema** | [mCIDE/microbiology_nonculture/](../mCIDE/microbiology_nonculture/) |
| **Result Column** | `result_category` |
| **Note** | PCR, antigen, molecular tests |
