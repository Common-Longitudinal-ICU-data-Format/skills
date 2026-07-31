import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    pat = pd.read_parquet(data_dir / "clif_patient.parquet",
                          columns=["patient_id", "race_category", "sex_category"])
    # Full cross-tabulation: every combination of an observed race_category
    # value x an observed sex_category value is a cell, even if that pairing
    # has zero patients (a zero-count cell is suppressed like any other).
    races = sorted(pat.race_category.unique())
    sexes = sorted(pat.sex_category.unique())
    full_index = pd.MultiIndex.from_product([races, sexes],
                                             names=["race_category", "sex_category"])
    counts = pat.groupby(["race_category", "sex_category"]).size().reindex(
        full_index, fill_value=0)
    suppressed = counts < 11
    return {"n_cells_total": int(len(counts)),
            "n_cells_suppressed": int(suppressed.sum()),
            "n_reported": int(counts[~suppressed].sum())}
