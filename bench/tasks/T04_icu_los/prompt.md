# T04: ICU length-of-stay
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), find every ICU stay interval: rows in the adt table whose
location_category indicates the ICU. For each such row compute its length
of stay in hours as (out_dttm - in_dttm). Write `solution.py` with
`solve(config_path: str) -> dict` returning:
{"n_icu_stays": <int>, "median_icu_los_hours": <float, 2dp>}
n_icu_stays counts ICU adt rows (one per ICU interval, not per
hospitalization — a hospitalization may contribute more than one ICU
interval). median_icu_los_hours is the median of the per-interval LOS in
hours across those rows.
Aggregates only — never return row-level records or ID lists.
