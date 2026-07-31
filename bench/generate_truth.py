#!/usr/bin/env python3
"""Maintainer-run: compute ground truth for bench tasks and write expected.json.

Truth code is written INDEPENDENTLY of the reference solutions (different
implementation where feasible) so a shared bug can't self-confirm.
Usage: python3 generate_truth.py [T01 T08 ...]   (default: all known)
"""
import json, sys
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / ".data" / "subset"
TASKS = Path(__file__).parent / "tasks"

def _pq(name, cols=None):
    return pd.read_parquet(DATA / f"clif_{name}.parquet", columns=cols)

def truth_T01_crrt_cohort():
    ids_crrt = set(_pq("crrt_therapy", ["hospitalization_id"]).hospitalization_id)
    ids_all = set(_pq("hospitalization", ["hospitalization_id"]).hospitalization_id)
    return {"n_crrt_hospitalizations": len(ids_crrt & ids_all) if ids_crrt <= ids_all else len(ids_crrt),
            "pct_of_all_hospitalizations": round(100 * len(ids_crrt) / len(ids_all), 2)}

def truth_T08_category_trap():
    rs = _pq("respiratory_support", ["hospitalization_id", "device_category"])
    by = rs.groupby("device_category")["hospitalization_id"].nunique()
    return {"n_hfnc_hospitalizations": int(by.get("High Flow NC", 0)),
            "n_imv_hospitalizations": int(by.get("IMV", 0))}

TRUTH = {name.split("truth_")[1]: fn for name, fn in list(globals().items())
         if name.startswith("truth_")}

def main(only=None):
    for task_id_name, fn in sorted(TRUTH.items()):
        tid = task_id_name.split("_")[0]
        if only and tid not in only:
            continue
        out = TASKS / task_id_name / "expected.json"
        out.write_text(json.dumps(fn(), indent=2) + "\n")
        print(f"wrote {out}")

if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
