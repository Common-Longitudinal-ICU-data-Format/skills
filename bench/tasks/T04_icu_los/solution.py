import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    adt = pd.read_parquet(data_dir / "clif_adt.parquet",
                          columns=["hospitalization_id", "location_category",
                                   "in_dttm", "out_dttm"])
    icu = adt.loc[adt.location_category == "icu"].copy()
    los_hours = (icu.out_dttm - icu.in_dttm).dt.total_seconds() / 3600
    return {"n_icu_stays": int(len(icu)),
            "median_icu_los_hours": round(float(los_hours.median()), 2)}
