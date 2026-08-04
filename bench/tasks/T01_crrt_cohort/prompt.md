# T01: CRRT cohort size
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), identify the CRRT cohort: every hospitalization that appears in
the crrt_therapy table. Write `solution.py` with
`solve(config_path: str) -> dict` returning:
{"n_crrt_hospitalizations": <int>, "pct_of_all_hospitalizations": <float 0-100, 2dp>}
Aggregates only — never return row-level records or ID lists.
