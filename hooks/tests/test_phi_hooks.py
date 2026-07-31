import json, os, subprocess, sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]

def run_hook(script, payload, env_extra=None, cwd=None):
    env = {**os.environ, **(env_extra or {})}
    p = subprocess.run([sys.executable, str(HOOKS / script)],
                       input=json.dumps(payload), text=True,
                       capture_output=True, env=env, cwd=cwd)
    return p.returncode, p.stdout, p.stderr

def payload(tool, **tool_input):
    return {"tool_name": tool, "tool_input": tool_input}

def test_no_config_allows_everything(tmp_path):
    rc, _, _ = run_hook("phi_guard.py", payload("Read", file_path="/anything/at/all.csv"),
                        env_extra={"CLIF_PHI_PATHS_FILE": str(tmp_path / "absent")},
                        cwd=tmp_path)
    assert rc == 0

def _cfg(tmp_path, *paths):
    f = tmp_path / "phi-paths"
    f.write_text("# site PHI dirs\n" + "\n".join(paths) + "\n")
    return {"CLIF_PHI_PATHS_FILE": str(f)}

def test_read_inside_phi_dir_blocked(tmp_path):
    phi = tmp_path / "real_data"; phi.mkdir()
    rc, _, err = run_hook("phi_guard.py",
        payload("Read", file_path=str(phi / "clif_labs.parquet")),
        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 2 and "PHI guard" in err

def test_read_outside_phi_dir_allowed(tmp_path):
    phi = tmp_path / "real_data"; phi.mkdir()
    ok = tmp_path / "dev_data"; ok.mkdir()
    rc, _, _ = run_hook("phi_guard.py",
        payload("Read", file_path=str(ok / "clif_labs.parquet")),
        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 0

def test_symlink_into_phi_dir_blocked(tmp_path):
    phi = tmp_path / "real_data"; phi.mkdir()
    (phi / "x.parquet").write_text("x")
    link = tmp_path / "innocent.parquet"; link.symlink_to(phi / "x.parquet")
    rc, _, _ = run_hook("phi_guard.py", payload("Read", file_path=str(link)),
                        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 2

def test_bash_command_mentioning_phi_path_blocked(tmp_path):
    phi = tmp_path / "real_data"; phi.mkdir()
    rc, _, _ = run_hook("phi_guard.py",
        payload("Bash", command=f"head -5 {phi}/clif_labs.csv"),
        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 2

def test_glob_path_key_blocked(tmp_path):
    phi = tmp_path / "real_data"; phi.mkdir()
    rc, _, _ = run_hook("phi_guard.py", payload("Glob", path=str(phi), pattern="*.parquet"),
                        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 2

def test_prefix_collision_not_blocked(tmp_path):
    # /a/real_data must not block /a/real_data_synth
    phi = tmp_path / "real_data"; phi.mkdir()
    other = tmp_path / "real_data_synth"; other.mkdir()
    rc, _, _ = run_hook("phi_guard.py", payload("Read", file_path=str(other / "f.parquet")),
                        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 0

def test_malformed_stdin_allows(tmp_path):
    p = subprocess.run([sys.executable, str(HOOKS / "phi_guard.py")], input="not json",
                       text=True, capture_output=True)
    assert p.returncode == 0  # fail-open on malformed input, never break the session

def test_case_variant_path_blocked(tmp_path):
    # macOS APFS case-insensitivity: /real_data configured, REAL_DATA/file.csv should still block
    phi = tmp_path / "real_data"; phi.mkdir()
    (phi / "labs.csv").write_text("x")
    # Use uppercase variant (on case-insensitive FS, this resolves to the same real_data dir)
    case_variant = str(tmp_path / "REAL_DATA" / "labs.csv")
    rc, _, _ = run_hook("phi_guard.py",
        payload("Read", file_path=case_variant),
        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 2

def test_json_array_payload_allows(tmp_path):
    # valid JSON but wrong shape: top-level array instead of object
    p = subprocess.run([sys.executable, str(HOOKS / "phi_guard.py")],
                       input='[{"tool_name":"Read"}]', text=True, capture_output=True)
    assert p.returncode == 0

def test_tool_input_string_allows(tmp_path):
    # valid JSON but tool_input is string instead of dict
    p = subprocess.run([sys.executable, str(HOOKS / "phi_guard.py")],
                       input='{"tool_name":"Read","tool_input":"oops"}',
                       text=True, capture_output=True)
    assert p.returncode == 0

def test_relative_path_inside_phi_dir_blocked(tmp_path):
    # relative file_path from within tmp_path (cwd)
    phi = tmp_path / "real_data"; phi.mkdir()
    (phi / "data.csv").write_text("x")
    rc, _, _ = run_hook("phi_guard.py",
        payload("Read", file_path="real_data/data.csv"),
        env_extra=_cfg(tmp_path, str(phi)), cwd=tmp_path)
    assert rc == 2

def test_crlf_line_endings_blocked(tmp_path):
    # config file with CRLF line endings should still parse correctly
    phi = tmp_path / "real_data"; phi.mkdir()
    cfg = tmp_path / "phi-paths"
    cfg.write_text("# comment\r\n" + str(phi) + "\r\n")
    rc, _, _ = run_hook("phi_guard.py",
        payload("Read", file_path=str(phi / "file.csv")),
        env_extra={"CLIF_PHI_PATHS_FILE": str(cfg)}, cwd=tmp_path)
    assert rc == 2

def test_scan_flags_mrn_pattern():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Bash", "tool_input": {"command": "cat notes.txt"},
        "tool_response": {"stdout": "Patient MRN: 84512937 admitted 03/14/1962"}})
    assert rc == 0
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "PHI-shaped" in ctx

def test_scan_flags_ssn_and_dob():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Read", "tool_input": {"file_path": "/x/notes.txt"},
        "tool_response": "SSN 123-45-6789, DOB: 1957-03-02"})
    assert json.loads(out)["hookSpecificOutput"]["additionalContext"]

def test_scan_silent_on_clean_output():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Bash", "tool_input": {"command": "pytest -q"},
        "tool_response": {"stdout": "14 passed in 3.2s"}})
    assert rc == 0 and out.strip() == ""

def test_scan_off_switch():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Bash", "tool_input": {},
        "tool_response": {"stdout": "MRN: 84512937"}},
        env_extra={"CLIF_PHI_SCAN": "off"})
    assert rc == 0 and out.strip() == ""

def test_scan_malformed_input_silent():
    p = subprocess.run([sys.executable, str(HOOKS / "phi_scan.py")], input="{",
                       text=True, capture_output=True)
    assert p.returncode == 0 and p.stdout.strip() == ""

def test_scan_nested_read_payload_flagged():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Read", "tool_input": {"file_path": "/x/notes.txt"},
        "tool_response": {"type": "text", "file": {"filePath": "x", "content": "MRN: 84512937"}}})
    assert rc == 0
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "PHI-shaped" in ctx

def test_scan_list_response_with_ssn_flagged():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Bash", "tool_input": {"command": "cat"},
        "tool_response": ["line 1", "SSN 123-45-6789", "line 3"]})
    assert rc == 0
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "PHI-shaped" in ctx

def test_scan_birth_date_column_flagged():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Read", "tool_input": {"file_path": "/x/data.csv"},
        "tool_response": {"data": "birth_date: 1975-05-02"}})
    assert rc == 0
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "PHI-shaped" in ctx

def test_scan_bare_timestamp_silent():
    rc, out, _ = run_hook("phi_scan.py", {
        "tool_name": "Bash", "tool_input": {"command": "date"},
        "tool_response": {"stdout": "recorded_dttm 2024-01-15T10:00:00"}})
    assert rc == 0 and out.strip() == ""
