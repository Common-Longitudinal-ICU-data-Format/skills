# T03: In-hospital mortality
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), compute in-hospital mortality across the hospitalization
cohort: a hospitalization counts as expired if its discharge_category
indicates death. Write `solution.py` with `solve(config_path: str) -> dict`
returning:
{"n_expired": <int>, "mortality_pct": <float 0-100, 2dp>}
mortality_pct = 100 * n_expired / (total hospitalizations).
Aggregates only — never return row-level records or ID lists.
