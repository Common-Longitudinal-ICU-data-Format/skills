"""clif-bench task loader and result comparator."""
import importlib.util
from pathlib import Path
import pytest

TASKS_DIR = Path(__file__).parent / "tasks"

def task_dirs():
    return sorted(p for p in TASKS_DIR.glob("T[0-9][0-9]_*") if p.is_dir())

def load_solution(task_dir):
    spec = importlib.util.spec_from_file_location(
        f"bench_{task_dir.name}", task_dir / "solution.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.solve

def assert_matches(result, expected, path=""):
    assert type(result) is type(expected) or (
        isinstance(result, (int, float)) and isinstance(expected, (int, float))
    ), f"{path}: type {type(result).__name__} != {type(expected).__name__}"
    if isinstance(expected, dict):
        # Metadata keys (e.g. "_clifpy_version") are not part of the scored
        # contract — skip them in both the key-set comparison and recursion so
        # solutions/truth can carry provenance without affecting scoring.
        result_keys = {k for k in result if not k.startswith("_")}
        expected_keys = {k for k in expected if not k.startswith("_")}
        assert result_keys == expected_keys, f"{path}: keys {result_keys} != {expected_keys}"
        for k in expected_keys:
            assert_matches(result[k], expected[k], f"{path}.{k}")
    elif isinstance(expected, list):
        assert len(result) == len(expected), f"{path}: length"
        for i, (r, e) in enumerate(zip(result, expected)):
            assert_matches(r, e, f"{path}[{i}]")
    elif isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4), f"{path}"
    else:
        assert result == expected, f"{path}: {result!r} != {expected!r}"
