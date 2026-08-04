import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    hosp = pd.read_parquet(data_dir / "clif_hospitalization.parquet",
                           columns=["hospitalization_id", "discharge_category"])
    n_expired = int((hosp.discharge_category == "Expired").sum())
    n_total = hosp.hospitalization_id.nunique()
    return {"n_expired": n_expired,
            "mortality_pct": round(100 * n_expired / n_total, 2)}
