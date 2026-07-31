import json
import pytest
from harness import task_dirs, load_solution, assert_matches

@pytest.mark.parametrize("task_dir", task_dirs(), ids=lambda p: p.name)
def test_task(task_dir, bench_config):
    expected_path = task_dir / "expected.json"
    if not expected_path.exists():
        pytest.fail(f"{task_dir.name}: expected.json missing — run generate_truth.py")
    expected = json.loads(expected_path.read_text())
    result = load_solution(task_dir)(bench_config)
    assert_matches(result, expected)
