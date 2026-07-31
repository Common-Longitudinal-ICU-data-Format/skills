#!/usr/bin/env bash
# Stand up the PINNED bench dataset in bench/.data (git-ignored).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REF="$(python3 -c "import json;print(json.load(open('$HERE/pin.json'))['ref'])")"
mkdir -p "$HERE/.data" && cd "$HERE/.data"
"$HERE/../skills/clif-icu/scripts/setup_dev_data.sh" \
  --source clif-forge-sample --ref "$REF" --config ./full_config.json ./full
python3 "$HERE/subset_bench_data.py" ./full ./subset
python3 - <<'PY'
from pathlib import Path
from clifpy.utils.config import create_example_config
# Absolute data_directory: config.json must resolve regardless of the caller's
# cwd (e.g. pytest invoked from bench/, not bench/.data/) — a relative
# "./subset" only works if the process happens to be cd'd into bench/.data.
create_example_config(data_directory=str(Path("./subset").resolve()), filetype="parquet",
                      timezone="US/Central", output_directory="./output",
                      config_path="./config.json")
PY
echo "bench data ready: bench/.data/config.json"
