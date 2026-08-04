import json
import numpy as np
import pandas as pd
from pathlib import Path


def _severinghaus(spo2):
    s = spo2 / 100.0
    a = 11700.0 / ((1 / s) - 1)
    b = np.sqrt(50 ** 3 + a ** 2)
    return (b + a) ** (1 / 3) - (b - a) ** (1 / 3)


def _bin(value, edges_scores, default=0):
    """edges_scores: list of (lower_bound_inclusive, score), checked in
    descending order of lower_bound. `value` NaN -> default."""
    if pd.isna(value):
        return default
    for lower, score in edges_scores:
        if value >= lower:
            return score
    return edges_scores[-1][1]


def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])

    def pq(name, cols=None):
        return pd.read_parquet(data_dir / f"clif_{name}.parquet", columns=cols)

    hosp = pq("hospitalization", ["hospitalization_id", "admission_dttm"])
    hosp["_hid_num"] = hosp.hospitalization_id.astype(int)
    cohort = hosp.sort_values("_hid_num").head(100).copy()
    cohort["window_end"] = cohort.admission_dttm + pd.Timedelta(hours=24)
    ids = set(cohort.hospitalization_id)
    win = cohort.set_index("hospitalization_id")[["admission_dttm", "window_end"]]

    def clip(df, tcol):
        df = df[df.hospitalization_id.isin(ids)].join(win, on="hospitalization_id")
        return df[(df[tcol] >= df.admission_dttm) & (df[tcol] < df.window_end)]

    labs = clip(pq("labs", ["hospitalization_id", "lab_order_dttm", "lab_category",
                             "lab_value_numeric"]), "lab_order_dttm")
    vitals = clip(pq("vitals", ["hospitalization_id", "recorded_dttm", "vital_category",
                                 "vital_value"]), "recorded_dttm")
    assess = clip(pq("patient_assessments", ["hospitalization_id", "recorded_dttm",
                                              "assessment_category", "numerical_value"]),
                  "recorded_dttm")
    resp = clip(pq("respiratory_support", ["hospitalization_id", "recorded_dttm", "fio2_set"]),
                "recorded_dttm")
    meds = clip(pq("medication_admin_continuous", ["hospitalization_id", "admin_dttm",
                                                     "med_category", "med_dose"]),
                "admin_dttm")

    po2_min = labs.loc[labs.lab_category == "po2_arterial"].groupby(
        "hospitalization_id").lab_value_numeric.min()
    plt_min = labs.loc[labs.lab_category == "platelet_count"].groupby(
        "hospitalization_id").lab_value_numeric.min()
    bili_max = labs.loc[labs.lab_category == "bilirubin_total"].groupby(
        "hospitalization_id").lab_value_numeric.max()
    creat_max = labs.loc[labs.lab_category == "creatinine"].groupby(
        "hospitalization_id").lab_value_numeric.max()
    map_min = vitals.loc[vitals.vital_category == "map"].groupby(
        "hospitalization_id").vital_value.min()
    spo2_min = vitals.loc[vitals.vital_category == "spo2"].groupby(
        "hospitalization_id").vital_value.min()
    gcs_min = assess.loc[assess.assessment_category == "gcs_total"].groupby(
        "hospitalization_id").numerical_value.min()
    fio2_max = resp.groupby("hospitalization_id").fio2_set.max()
    norepi_max = meds.loc[meds.med_category == "norepinephrine"].groupby(
        "hospitalization_id").med_dose.max()

    totals = []
    for hid in cohort.hospitalization_id:
        pao2 = po2_min.get(hid, np.nan)
        if pd.isna(pao2):
            spo2 = spo2_min.get(hid, np.nan)
            pao2 = _severinghaus(spo2) if (not pd.isna(spo2) and spo2 < 97) else np.nan
        fio2 = fio2_max.get(hid, np.nan)
        fio2 = 0.21 if pd.isna(fio2) else fio2
        pf = np.nan if pd.isna(pao2) else pao2 / fio2
        resp_score = _bin(pf, [(400, 0), (300, 1), (200, 2), (100, 3), (-np.inf, 4)])

        coag_score = _bin(plt_min.get(hid, np.nan),
                           [(150, 0), (100, 1), (50, 2), (20, 3), (-np.inf, 4)])
        liver_score = _bin(bili_max.get(hid, np.nan),
                            [(12.0, 4), (6.0, 3), (2.0, 2), (1.2, 1), (-np.inf, 0)])
        renal_score = _bin(creat_max.get(hid, np.nan),
                            [(5.0, 4), (3.5, 3), (2.0, 2), (1.2, 1), (-np.inf, 0)])
        gcs = gcs_min.get(hid, np.nan)
        if pd.isna(gcs):
            cns_score = 0
        elif gcs >= 15:
            cns_score = 0
        else:
            cns_score = _bin(gcs, [(13, 1), (10, 2), (6, 3), (-np.inf, 4)])

        norepi = norepi_max.get(hid, np.nan)
        norepi = 0.0 if pd.isna(norepi) else norepi
        mapv = map_min.get(hid, np.nan)
        if norepi > 0.1:
            cv_score = 4
        elif norepi > 0:
            cv_score = 3
        elif not pd.isna(mapv) and mapv < 70:
            cv_score = 1
        else:
            cv_score = 0

        totals.append(resp_score + coag_score + liver_score + cv_score + cns_score + renal_score)

    totals = pd.Series(totals, dtype=float)
    return {"n_scored": int(len(totals)),
            "mean_day1_sofa": round(float(totals.mean()), 2)}
