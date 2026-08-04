#!/usr/bin/env python3
"""Maintainer-run: compute ground truth for bench tasks and write expected.json.

Truth code is written INDEPENDENTLY of the reference solutions (different
implementation where feasible) so a shared bug can't self-confirm.
Usage: python3 generate_truth.py [T01 T08 ...]   (default: all known)
"""
import json, re, sys
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).parent / ".data" / "subset"
TASKS = Path(__file__).parent / "tasks"
REPO_ROOT = Path(__file__).parent.parent

def _pq(name, cols=None):
    return pd.read_parquet(DATA / f"clif_{name}.parquet", columns=cols)

def truth_T01_crrt_cohort():
    ids_crrt = set(_pq("crrt_therapy", ["hospitalization_id"]).hospitalization_id)
    ids_all = set(_pq("hospitalization", ["hospitalization_id"]).hospitalization_id)
    orphans = ids_crrt - ids_all
    if orphans:
        raise ValueError(
            f"T01 truth: crrt_therapy has {len(orphans)} hospitalization_id(s) "
            f"absent from the hospitalization table (referential-integrity "
            f"violation) — e.g. {sorted(orphans)[:5]}")
    return {"n_crrt_hospitalizations": len(ids_crrt),
            "pct_of_all_hospitalizations": round(100 * len(ids_crrt) / len(ids_all), 2)}

def truth_T08_category_trap():
    rs = _pq("respiratory_support", ["hospitalization_id", "device_category"])
    by = rs.groupby("device_category")["hospitalization_id"].nunique()
    return {"n_hfnc_hospitalizations": int(by.get("High Flow NC", 0)),
            "n_imv_hospitalizations": int(by.get("IMV", 0))}

def truth_T02_imv_cohort():
    # Set arithmetic (not solution.py's groupby/nunique) so a shared bug in
    # one path doesn't self-confirm the other.
    rs = _pq("respiratory_support", ["hospitalization_id", "device_category"])
    ids_imv = set(rs.loc[rs.device_category == "IMV", "hospitalization_id"])
    return {"n_imv_hospitalizations": len(ids_imv)}

def truth_T03_mortality():
    hosp = _pq("hospitalization", ["hospitalization_id", "discharge_category"])
    counts = hosp.discharge_category.value_counts()
    n_expired = int(counts.get("Expired", 0))
    n_total = len(hosp)
    return {"n_expired": n_expired,
            "mortality_pct": round(100 * n_expired / n_total, 2)}

def truth_T04_icu_los():
    # Integer epoch-microsecond arithmetic (this subset's datetime64 columns
    # are microsecond-precision) instead of solution.py's
    # Timedelta.total_seconds(); numpy median instead of pandas .median().
    adt = _pq("adt", ["hospitalization_id", "location_category", "in_dttm", "out_dttm"])
    icu = adt.loc[adt.location_category == "icu"]
    los_hours = (icu.out_dttm.astype("int64") - icu.in_dttm.astype("int64")) / 3.6e9
    return {"n_icu_stays": int(len(icu)),
            "median_icu_los_hours": round(float(np.median(los_hours)), 2)}

def truth_T05_norepi_dose():
    # Hand-computed directly from med_dose/med_dose_unit (no clifpy unit
    # converter) — valid because norepinephrine doses in this subset are
    # uniformly recorded in mcg/kg/min already (verified below).
    mac = _pq("medication_admin_continuous",
              ["hospitalization_id", "med_category", "med_dose", "med_dose_unit"])
    norepi = mac.loc[mac.med_category == "norepinephrine"]
    units = set(norepi.med_dose_unit.unique())
    if units != {"mcg/kg/min"}:
        raise ValueError(f"T05 truth assumes uniform mcg/kg/min norepinephrine dosing; "
                          f"found units {units} — hand-conversion needed, revisit truth fn")
    peak = norepi.groupby("hospitalization_id").med_dose.max()
    return {"n_norepi_hospitalizations": int(len(peak)),
            "median_peak_dose_mcg_kg_min": round(float(peak.median()), 2)}

def truth_T06_day1_sofa():
    # Independent-implementations pair (see bench/README.md): clifpy 0.5.0's
    # compute_sofa_scores() cannot be run headlessly against this pinned
    # subset restricted to a day-1 cohort window, so both solution.py and
    # this truth fn implement the same documented SOFA rubric (prompt.md)
    # directly in pandas, via genuinely different code shapes: solution.py
    # loops per-hospitalization with scalar helper functions; this fn is
    # fully vectorized (merge-based wide table + numpy.select bin edges).
    hosp = _pq("hospitalization", ["hospitalization_id", "admission_dttm"])
    hosp["_hid_num"] = hosp.hospitalization_id.astype(int)
    cohort = hosp.sort_values("_hid_num").head(100).copy()
    cohort["window_end"] = cohort.admission_dttm + pd.Timedelta(hours=24)
    ids = set(cohort.hospitalization_id)
    win = cohort.set_index("hospitalization_id")[["admission_dttm", "window_end"]]

    def clip(df, tcol):
        df = df[df.hospitalization_id.isin(ids)].join(win, on="hospitalization_id")
        return df[(df[tcol] >= df.admission_dttm) & (df[tcol] < df.window_end)]

    labs = clip(_pq("labs", ["hospitalization_id", "lab_order_dttm", "lab_category",
                              "lab_value_numeric"]), "lab_order_dttm")
    vitals = clip(_pq("vitals", ["hospitalization_id", "recorded_dttm", "vital_category",
                                  "vital_value"]), "recorded_dttm")
    assess = clip(_pq("patient_assessments", ["hospitalization_id", "recorded_dttm",
                                               "assessment_category", "numerical_value"]),
                  "recorded_dttm")
    resp = clip(_pq("respiratory_support", ["hospitalization_id", "recorded_dttm", "fio2_set"]),
                "recorded_dttm")
    meds = clip(_pq("medication_admin_continuous", ["hospitalization_id", "admin_dttm",
                                                      "med_category", "med_dose"]),
                "admin_dttm")

    wide = pd.DataFrame(index=cohort.hospitalization_id)
    wide["po2_min"] = labs.loc[labs.lab_category == "po2_arterial"].groupby(
        "hospitalization_id").lab_value_numeric.min()
    wide["spo2_min"] = vitals.loc[vitals.vital_category == "spo2"].groupby(
        "hospitalization_id").vital_value.min()
    wide["fio2_max"] = resp.groupby("hospitalization_id").fio2_set.max()
    wide["plt_min"] = labs.loc[labs.lab_category == "platelet_count"].groupby(
        "hospitalization_id").lab_value_numeric.min()
    wide["bili_max"] = labs.loc[labs.lab_category == "bilirubin_total"].groupby(
        "hospitalization_id").lab_value_numeric.max()
    wide["creat_max"] = labs.loc[labs.lab_category == "creatinine"].groupby(
        "hospitalization_id").lab_value_numeric.max()
    wide["map_min"] = vitals.loc[vitals.vital_category == "map"].groupby(
        "hospitalization_id").vital_value.min()
    wide["gcs_min"] = assess.loc[assess.assessment_category == "gcs_total"].groupby(
        "hospitalization_id").numerical_value.min()
    wide["norepi_max"] = meds.loc[meds.med_category == "norepinephrine"].groupby(
        "hospitalization_id").med_dose.max()
    wide["norepi_max"] = wide["norepi_max"].fillna(0.0)

    # Severinghaus imputation of PaO2 from SpO2 (<97) where po2_arterial missing.
    s = wide.spo2_min / 100.0
    a = 11700.0 / ((1 / s) - 1)
    b = np.sqrt(50 ** 3 + a ** 2)
    pao2_imputed = (b + a) ** (1 / 3) - (b - a) ** (1 / 3)
    pao2_imputed = pao2_imputed.where(wide.spo2_min < 97)
    pao2 = wide.po2_min.fillna(pao2_imputed)
    fio2 = wide.fio2_max.fillna(0.21)
    pf = pao2 / fio2

    wide["resp"] = np.select(
        [pf >= 400, pf >= 300, pf >= 200, pf >= 100, pf.notna()],
        [0, 1, 2, 3, 4], default=0)
    wide["coag"] = np.select(
        [wide.plt_min >= 150, wide.plt_min >= 100, wide.plt_min >= 50, wide.plt_min >= 20,
         wide.plt_min.notna()],
        [0, 1, 2, 3, 4], default=0)
    wide["liver"] = np.select(
        [wide.bili_max >= 12.0, wide.bili_max >= 6.0, wide.bili_max >= 2.0, wide.bili_max >= 1.2,
         wide.bili_max.notna()],
        [4, 3, 2, 1, 0], default=0)
    wide["renal"] = np.select(
        [wide.creat_max >= 5.0, wide.creat_max >= 3.5, wide.creat_max >= 2.0, wide.creat_max >= 1.2,
         wide.creat_max.notna()],
        [4, 3, 2, 1, 0], default=0)
    wide["cns"] = np.select(
        [wide.gcs_min >= 15, wide.gcs_min >= 13, wide.gcs_min >= 10, wide.gcs_min >= 6,
         wide.gcs_min.notna()],
        [0, 1, 2, 3, 4], default=0)
    wide["cv"] = np.select(
        [wide.norepi_max > 0.1, wide.norepi_max > 0, wide.map_min < 70],
        [4, 3, 1], default=0)

    total = wide[["resp", "coag", "liver", "cv", "cns", "renal"]].sum(axis=1)
    return {"n_scored": int(len(total)), "mean_day1_sofa": round(float(total.mean()), 2)}

def truth_T07_hourly_wide():
    # Pure pandas, independent of clifpy's create_wide_dataset/
    # convert_wide_to_hourly (see bench/README.md T07 note on the chosen
    # admission-anchored hourly binning semantic).
    hosp = _pq("hospitalization", ["hospitalization_id", "admission_dttm"])
    hosp["_hid_num"] = hosp.hospitalization_id.astype(int)
    first20 = hosp.sort_values("_hid_num").head(20)
    ids = set(first20.hospitalization_id)

    vit = _pq("vitals", ["hospitalization_id", "recorded_dttm", "vital_category", "vital_value"])
    hr = vit.loc[(vit.hospitalization_id.isin(ids)) & (vit.vital_category == "heart_rate")].copy()
    hr = hr.merge(first20[["hospitalization_id", "admission_dttm"]], on="hospitalization_id")
    hr["hour_bin"] = np.floor((hr.recorded_dttm - hr.admission_dttm) / pd.Timedelta(hours=1)).astype(int)

    hourly = hr.groupby(["hospitalization_id", "hour_bin"]).vital_value.mean()
    return {"n_rows": int(len(hourly)), "mean_heart_rate": round(float(hourly.mean()), 2)}

def truth_T09_small_cell():
    # pd.crosstab (not solution.py's groupby.size()).
    pat = _pq("patient", ["patient_id", "race_category", "sex_category"])
    ct = pd.crosstab(pat.race_category, pat.sex_category)
    counts = ct.values.flatten()
    suppressed = counts < 11
    return {"n_cells_total": int(counts.size),
            "n_cells_suppressed": int(suppressed.sum()),
            "n_reported": int(counts[~suppressed].sum())}

def truth_T10_potassium_outliers():
    # Regex-parse the outlier config yaml (not solution.py's yaml.safe_load).
    labs = _pq("labs", ["hospitalization_id", "lab_category", "lab_value_numeric"])
    k = labs.loc[labs.lab_category == "potassium", "lab_value_numeric"]

    schema_path = REPO_ROOT / "skills" / "clif-icu" / "schemas" / "outlier_config.yaml"
    text = schema_path.read_text()
    m = re.search(r"potassium:\s*\n\s*min:\s*([\d.]+)\s*\n\s*max:\s*([\d.]+)", text)
    lo, hi = float(m.group(1)), float(m.group(2))

    n_outside = int(((k < lo) | (k > hi)).sum())
    return {"n_potassium_values": int(len(k)), "n_outside_range": n_outside}

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
