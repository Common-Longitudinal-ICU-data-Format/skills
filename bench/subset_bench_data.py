#!/usr/bin/env python3
"""Deterministic bench subset: first N hospitalization_ids (ascending numeric)."""
import json, shutil, sys
from pathlib import Path
import pandas as pd

def main(src, dst, n=None):
    src, dst = Path(src), Path(dst)
    n = n or json.load(open(Path(__file__).parent / "pin.json"))["subset"]["n_hospitalizations"]
    dst.mkdir(parents=True, exist_ok=True)
    hosp = pd.read_parquet(src / "clif_hospitalization.parquet")
    ids = hosp["hospitalization_id"].drop_duplicates().sort_values(
        key=lambda s: pd.to_numeric(s, errors="coerce")).head(n)
    keep_h = set(ids)
    keep_p = set(hosp[hosp.hospitalization_id.isin(keep_h)]["patient_id"])
    for f in sorted(src.glob("clif_*.parquet")):
        df = pd.read_parquet(f)
        if "hospitalization_id" in df.columns:
            df = df[df.hospitalization_id.isin(keep_h)]
        elif "patient_id" in df.columns:
            df = df[df.patient_id.isin(keep_p)]
        # tables keyed some other way (e.g. provider): keep whole
        df.to_parquet(dst / f.name, index=False)
    print(f"subset: {len(keep_h)} hospitalizations, {len(keep_p)} patients -> {dst}")

if __name__ == "__main__":
    main(*sys.argv[1:3])
