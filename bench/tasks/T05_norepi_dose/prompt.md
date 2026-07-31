# T05: Peak norepinephrine dose
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), identify every hospitalization that received norepinephrine
(medication_admin_continuous, med_category per the mCIDE). For each such
hospitalization, find its maximum standardized norepinephrine dose in
mcg/kg/min across the whole medication_admin_continuous record for that
hospitalization. Write `solution.py` with `solve(config_path: str) -> dict`
returning:
{"n_norepi_hospitalizations": <int>, "median_peak_dose_mcg_kg_min": <float, 2dp>}
median_peak_dose_mcg_kg_min is the median, across those hospitalizations, of
each hospitalization's own peak (maximum) standardized dose.
Aggregates only — never return row-level records or ID lists.
