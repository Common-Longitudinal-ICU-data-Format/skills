import json
from pathlib import Path
from clifpy import ClifOrchestrator

def solve(config_path: str) -> dict:
    co = ClifOrchestrator(config_path=config_path)
    co.convert_dose_units_for_continuous_meds(
        preferred_units={"norepinephrine": "mcg/kg/min"})
    dfc = co.medication_admin_continuous.df_converted
    norepi = dfc.loc[dfc.med_category == "norepinephrine"]
    peak = norepi.groupby("hospitalization_id")["med_dose_converted"].max()
    return {"n_norepi_hospitalizations": int(len(peak)),
            "median_peak_dose_mcg_kg_min": round(float(peak.median()), 2)}
