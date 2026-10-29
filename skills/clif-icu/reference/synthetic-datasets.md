# Choose synthetic CLIF inputs

Use small, fully synthetic fixtures for agent-assisted coding, tests, and demos.
A supplied or in-memory R/Python fixture is sufficient; a generator is optional.
Match the fixture to the user's declared CLIF version and current mCIDE.

For larger synthetic inputs, inspect the current instructions, license, and
provenance of [synthetic_clif](https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif)
or [clif-forge](https://github.com/sajor2000/clif-forge). Pin a release or commit
and seed for reproducibility. Do not assume a generator emits the newest CLIF version.

The optional helper requires Bash and its documented Python dependencies.
From the skill root:

```bash
bash scripts/setup_dev_data.sh --source clif-forge-sample ./dev_data
bash scripts/setup_dev_data.sh --source synthetic-clif ./dev_data 100
bash scripts/setup_dev_data.sh --source clif-forge-generate ./dev_data 500
```

Credentialed or real-derived datasets, including MIMIC-IV-Ext-CLIF, are not
synthetic test inputs for this workflow. The researcher handles any approved
restricted-data download and execution separately, with the agent absent.
A BAA or covered channel does not create an exception to the skill's
[synthetic-only boundary](phi-safe-development.md).

Synthetic results validate code behavior; they are not clinical evidence.
