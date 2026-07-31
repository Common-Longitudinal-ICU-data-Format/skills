import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    pat = pd.read_parquet(data_dir / "clif_patient.parquet",
                          columns=["patient_id", "race_category", "sex_category"])
    counts = pat.groupby(["race_category", "sex_category"]).size()
    suppressed = counts < 11
    return {"n_cells_total": int(len(counts)),
            "n_cells_suppressed": int(suppressed.sum()),
            "n_reported": int(counts[~suppressed].sum())}
