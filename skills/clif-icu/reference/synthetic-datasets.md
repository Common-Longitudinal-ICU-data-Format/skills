# Choosing a synthetic CLIF dataset

Three non-PHI options; all emit CLIF 2.1. None contain real patient data.

| | synthetic_clif | clif-forge | MIMIC-IV-Ext-CLIF |
|---|---|---|---|
| Method | hand-specified priors | empirically calibrated to aggregate CLIF stats | derived from real MIMIC-IV |
| Tables | 28 | ~20 | CLIF core |
| Redistribution | MIT, free | free, openly redistributable | PhysioNet credentialed — NOT shareable with agents on uncovered channels |
| Realism | schema-true, priors-based | lands in the real statistical region | real-derived |
| Fastest path | 10k release download | committed in-repo sample (clone-and-go) | credentialed download |
| Reproducible recipe | seed-based CLI | TOML spec + seed | n/a |
| Upstream | [github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif](https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif) v0.7.0 | [github.com/sajor2000/clif-forge](https://github.com/sajor2000/clif-forge) (no tags; pinned SHA c29e0e0) | [PhysioNet MIMIC-IV-Ext-CLIF](https://physionet.org/content/mimic-iv-ext-clif/1.1.0/) |

**Rules of thumb**
- Agent-assisted development, demos, CI: `clif-forge-sample` (fastest, redistributable) or `synthetic_clif`.
- Statistical realism (model prototyping, plausibility checks): `clif-forge` (calibrated) — still synthetic; never publish inferences from it.
- Validating against real-world messiness: MIMIC-IV-Ext-CLIF — but treat as restricted data; see the BAA/channel rules in [phi-safe-development.md](phi-safe-development.md) before letting ANY agent see it.
- clif-bench (this repo's benchmark suite, landing in bench/) will pin `clif-forge-sample` for its ground truth.

One command for each (from skill root):
```bash
./scripts/setup_dev_data.sh --source clif-forge-sample ./dev_data     # fastest
./scripts/setup_dev_data.sh --source synthetic-clif ./dev_data 100    # 28 tables, generated
./scripts/setup_dev_data.sh --source clif-forge-generate ./dev_data 500  # custom recipe
```

---

**Verified 2026-07-31, re-check tags before relying.** clif-forge has no version tags upstream; pinned by main-branch SHA for reproducibility.
