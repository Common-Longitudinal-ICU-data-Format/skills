import json
import yaml
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    labs = pd.read_parquet(data_dir / "clif_labs.parquet",
                           columns=["hospitalization_id", "lab_category", "lab_value_numeric"])
    k = labs.loc[labs.lab_category == "potassium", "lab_value_numeric"]

    schema_path = Path(__file__).resolve().parents[3] / "skills" / "clif-icu" / "schemas" / "outlier_config.yaml"
    cfg = yaml.safe_load(schema_path.read_text())
    bounds = cfg["tables"]["labs"]["lab_value_numeric"]["potassium"]
    lo, hi = bounds["min"], bounds["max"]

    n_outside = int(((k < lo) | (k > hi)).sum())
    return {"n_potassium_values": int(len(k)), "n_outside_range": n_outside}
