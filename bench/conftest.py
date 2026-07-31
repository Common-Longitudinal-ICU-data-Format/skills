import json
from pathlib import Path
import pytest

@pytest.fixture(scope="session")
def bench_config():
    cfg = Path(__file__).parent / ".data" / "config.json"
    if not cfg.exists():
        pytest.skip("bench data missing — run bench/setup_bench_data.sh first")
    return str(cfg)
