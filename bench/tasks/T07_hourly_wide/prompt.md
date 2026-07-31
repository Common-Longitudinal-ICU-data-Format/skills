# T07: Hourly heart rate summary
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), build an hourly-binned summary of heart_rate for the first 20
hospitalizations in the dataset, ordered by hospitalization_id ascending
(numeric order).

Binning definition (use exactly this, per hospitalization): hour 0 is
`[admission_dttm, admission_dttm + 1 hour)`, hour k is
`[admission_dttm + k hours, admission_dttm + (k+1) hours)`, where
admission_dttm comes from the hospitalization table. This is an
admission-anchored hourly grid, not a wall-clock floor-to-the-hour grid.
Assign every heart_rate vital reading (vitals table, vital_category
"heart_rate") for these 20 hospitalizations to its hour bin, then take the
mean heart_rate within each (hospitalization_id, hour bin) group. Only
include (hospitalization_id, hour bin) groups that have at least one
heart_rate reading — do not emit empty hourly rows for hours with no data.

Write `solution.py` with `solve(config_path: str) -> dict` returning:
{"n_rows": <int>, "mean_heart_rate": <float, 2dp>}
n_rows is the number of non-empty (hospitalization_id, hour bin) rows in
the hourly table described above. mean_heart_rate is the mean of that
table's per-row mean heart_rate values (i.e. the mean of the hourly means,
not the mean of every raw reading).
Aggregates only — never return row-level records or ID lists.
