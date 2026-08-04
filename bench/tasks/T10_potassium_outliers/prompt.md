# T10: Potassium outlier count
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), find every potassium lab value (labs table, lab_category
"potassium", lab_value_numeric) and count how many fall outside the
clinically plausible range defined by the CLIF outlier configuration
(`skills/clif-icu/schemas/outlier_config.yaml`, tables.labs.lab_value_numeric.
potassium). A value is "outside range" if it is strictly less than the
configured min or strictly greater than the configured max (values exactly
at the boundary are in-range). Write `solution.py` with
`solve(config_path: str) -> dict` returning:
{"n_potassium_values": <int>, "n_outside_range": <int>}
n_potassium_values is the total count of potassium lab rows (numerator and
denominator population); n_outside_range is how many of those fall outside
[min, max].
Aggregates only — never return row-level records or ID lists.
