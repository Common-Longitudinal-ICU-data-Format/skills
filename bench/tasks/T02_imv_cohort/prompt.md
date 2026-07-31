# T02: Invasive mechanical ventilation cohort size
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), identify every hospitalization that ever appears in the
respiratory_support table with an invasive-mechanical-ventilation device
recorded. Write `solution.py` with `solve(config_path: str) -> dict`
returning:
{"n_imv_hospitalizations": <int>}
Aggregates only — never return row-level records or ID lists.
