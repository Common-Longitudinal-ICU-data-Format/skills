import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    crrt = pd.read_parquet(data_dir / "clif_crrt_therapy.parquet",
                           columns=["hospitalization_id"])
    hosp = pd.read_parquet(data_dir / "clif_hospitalization.parquet",
                           columns=["hospitalization_id"])
    n = crrt.hospitalization_id.nunique()
    return {"n_crrt_hospitalizations": int(n),
            "pct_of_all_hospitalizations": round(100 * n / hosp.hospitalization_id.nunique(), 2)}
