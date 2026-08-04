import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    rs = pd.read_parquet(data_dir / "clif_respiratory_support.parquet",
                         columns=["hospitalization_id", "device_category"])
    def n_with(cat):
        return int(rs.loc[rs.device_category == cat, "hospitalization_id"].nunique())
    return {"n_hfnc_hospitalizations": n_with("High Flow NC"),
            "n_imv_hospitalizations": n_with("IMV")}
