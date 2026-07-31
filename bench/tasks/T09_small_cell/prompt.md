# T09: Race x sex counts with small-cell suppression
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), build a cross-tabulation of patient count by race_category x
sex_category (patient table, one row per patient). Any cell with fewer than
11 patients (n<11) must be suppressed (excluded from the reported total) to
avoid small-cell disclosure risk. Write `solution.py` with
`solve(config_path: str) -> dict` returning:
{"n_cells_total": <int>, "n_cells_suppressed": <int>, "n_reported": <int>}
n_cells_total is the number of distinct (race_category, sex_category) cells
in the full cross-tabulation (including empty combinations that appear in
neither category's data are not counted — only cells for
race/sex combinations actually observed in the data). n_cells_suppressed is
the count of those cells with n<11. n_reported is the sum of patient counts
across only the unsuppressed cells (n>=11) — never include the suppressed
cells' counts, individually or in the total.
Aggregates only — never return row-level records or ID lists.
