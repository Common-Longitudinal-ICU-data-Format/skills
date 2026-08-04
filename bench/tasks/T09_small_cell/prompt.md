# T09: Race x sex counts with small-cell suppression
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), build a cross-tabulation of patient count by race_category x
sex_category (patient table, one row per patient). Any cell with fewer than
11 patients (n<11) must be suppressed (excluded from the reported total) to
avoid small-cell disclosure risk. Write `solution.py` with
`solve(config_path: str) -> dict` returning:
{"n_cells_total": <int>, "n_cells_suppressed": <int>, "n_reported": <int>}
n_cells_total is the number of cells in the full cross-tabulation: every
combination of a race_category value and a sex_category value observed
anywhere in the data (the cartesian product of the distinct race_category
values observed x the distinct sex_category values observed). A combination
with zero patients still counts as a cell, with n=0 — and n=0 is below the
suppression threshold, so it is suppressed like any other small cell.
n_cells_suppressed is the count of cells with n<11 (including any
zero-count cells). n_reported is the sum of patient counts across only the
unsuppressed cells (n>=11) — never include the suppressed cells' counts,
individually or in the total.
Aggregates only — never return row-level records or ID lists.
