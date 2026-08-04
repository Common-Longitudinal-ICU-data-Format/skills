import json
import numpy as np
import pandas as pd
from pathlib import Path
from clifpy import ClifOrchestrator

def solve(config_path: str) -> dict:
    co = ClifOrchestrator(config_path=config_path)
    hosp = pd.read_parquet(
        Path(json.load(open(config_path))["data_directory"]) / "clif_hospitalization.parquet",
        columns=["hospitalization_id", "admission_dttm"])
    hosp["_hid_num"] = hosp.hospitalization_id.astype(int)
    first20 = hosp.sort_values("_hid_num").head(20).copy()

    # clifpy table-level load (validated against config/schema), filtered to
    # this cohort and the heart_rate category only.
    co.load_table("vitals", filters={
        "hospitalization_id": first20.hospitalization_id.astype(str).tolist(),
        "vital_category": ["heart_rate"],
    })
    hr = co.vitals.df.copy()
    hr["hospitalization_id"] = hr["hospitalization_id"].astype("int64")

    hr = hr.merge(first20[["hospitalization_id", "admission_dttm"]], on="hospitalization_id")
    delta_hours = (hr.recorded_dttm - hr.admission_dttm) / pd.Timedelta(hours=1)
    hr["hour_bin"] = np.floor(delta_hours).astype(int)

    hourly = hr.groupby(["hospitalization_id", "hour_bin"])["vital_value"].mean()
    return {"n_rows": int(len(hourly)),
            "mean_heart_rate": round(float(hourly.mean()), 2)}
