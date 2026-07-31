# T06: Mean day-1 SOFA score
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), compute the day-1 SOFA (Sequential Organ Failure Assessment)
total score for the first 100 hospitalizations in the dataset, ordered by
hospitalization_id ascending (numeric order). "Day 1" for a hospitalization
is the window [admission_dttm, admission_dttm + 24 hours) — use the
hospitalization table's admission_dttm as the window start.

Score each of the six standard SOFA components 0-4 using the **worst**
(most deranged) value observed for that hospitalization within its day-1
window, then sum the six components for a total 0-24. If a component's
underlying data element has zero observations in the window for a given
hospitalization, score that component 0 (i.e. missing data defaults to
"organ system assumed normal", not to a missing/NaN total). Use exactly
these rules:

- **Respiratory** (PaO2/FiO2 ratio, mmHg): PaO2 = the minimum
  `po2_arterial` lab value in the window. If no `po2_arterial` lab exists in
  the window but a `spo2` vital does, and the minimum `spo2` in the window
  is < 97, impute PaO2 from that minimum SpO2 via the Severinghaus equation:
  `s = spo2/100; a = 11700/((1/s)-1); b = sqrt(50**3 + a**2);
  pao2 = (b+a)**(1/3) - (b-a)**(1/3)`. FiO2 = the maximum `fio2_set` in the
  window from respiratory_support; if no respiratory_support row exists in
  the window, default FiO2 to 0.21 (room air). Score PF = PaO2/FiO2 as:
  >=400 -> 0, 300-399 -> 1, 200-299 -> 2, 100-199 -> 3, <100 -> 4.
- **Coagulation** (platelets, x10^3/uL): minimum `platelet_count` lab value
  in the window. Score: >=150 -> 0, 100-149 -> 1, 50-99 -> 2, 20-49 -> 3,
  <20 -> 4.
- **Liver** (bilirubin, mg/dL): maximum `bilirubin_total` lab value in the
  window. Score: <1.2 -> 0, 1.2-1.9 -> 1, 2.0-5.9 -> 2, 6.0-11.9 -> 3,
  >=12.0 -> 4.
- **Cardiovascular**: minimum `map` vital in the window, and maximum
  norepinephrine dose (medication_admin_continuous, med_category
  "norepinephrine", med_dose in its recorded med_dose_unit — this dataset
  records norepinephrine doses natively in mcg/kg/min, no conversion
  needed) in the window. Score: norepinephrine dose > 0.1 mcg/kg/min -> 4;
  0 < dose <= 0.1 mcg/kg/min -> 3; no norepinephrine and MAP < 70 -> 1;
  no norepinephrine and (MAP >= 70 or MAP not observed) -> 0. (Other
  vasoactive agents are intentionally excluded from this component — see
  bench/README.md for why.)
- **CNS** (Glasgow Coma Scale): minimum `gcs_total` value from
  patient_assessments in the window. Score: 15 -> 0, 13-14 -> 1, 10-12 -> 2,
  6-9 -> 3, <6 -> 4.
- **Renal** (creatinine, mg/dL): maximum `creatinine` lab value in the
  window. Score: <1.2 -> 0, 1.2-1.9 -> 1, 2.0-3.4 -> 2, 3.5-4.9 -> 3,
  >=5.0 -> 4.

Write `solution.py` with `solve(config_path: str) -> dict` returning:
{"n_scored": <int>, "mean_day1_sofa": <float, 2dp>}
n_scored is the number of hospitalizations scored (100, unless fewer than
100 hospitalizations exist in the dataset). mean_day1_sofa is the mean of
the six-component total across those hospitalizations.
Aggregates only — never return row-level records or ID lists.
