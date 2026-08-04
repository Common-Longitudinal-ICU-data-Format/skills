# Sprint 1: Trust Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the trust layer for consortium AI adoption: a multi-source non-PHI sandbox, mechanical PHI guardrail hooks, a golden-task benchmark (clif-bench v0), and three distributable agents — all in this skills repo, installed by one `/plugin install`.

**Architecture:** Everything lives in this repo (the plugin root). The two synthetic-data repos are consumed by pinned clone; clifpy is the ground-truth engine. Hooks and agents wire into the existing `.claude-plugin/marketplace.json` plugin entry. Bench is plain pytest over per-task `prompt.md`/`solution.py`/`expected.json` triples.

**Tech Stack:** bash (sandbox script + its stub-based tests), Python 3 stdlib (hooks — no third-party deps), pytest + pandas + clifpy (bench), markdown (agents, memo).

**Spec:** `docs/plans/2026-07-31-005-sprint1-trust-layer-design.md`

## Global Constraints

- Branch: all work on `sprint1-trust-layer`. Commits at task boundaries only. **Never push or open a PR without Kaveri's explicit permission.**
- No real/PHI data anywhere: no PHI paths, no real-site names in examples, no credentialed datasets (MIMIC) committed or downloaded.
- Pins: synthetic_clif `v0.7.0` (existing default); clif-forge `v0.2.0` (verify `sample_dataset/` exists at that tag in Task 1; if absent, pin the current `main` SHA instead and record it in `bench/pin.json`).
- Hook scripts: Python 3 **stdlib only** (sites must not need extra installs for guardrails). Shebang `#!/usr/bin/env python3`.
- Bash tests are network-free (stub `git`/`python3` on PATH), matching `scripts/tests/test_setup_dev_data.sh` style.
- Never assert a clifpy API from memory: before using a clifpy symbol in bench truth/solutions, verify with `python3 -c "import inspect, clifpy; ..."` (`inspect.signature`, `inspect.getdoc`).
- All bench expected values are **aggregates** (counts, medians, means) — never row-level dumps — modeling small-cell discipline even on synthetic data.
- Existing behavior is contract: default (no-flag) `setup_dev_data.sh` invocation must behave exactly as today; all existing tests keep passing.
- Plugin manifest version bumps `1.2.0` → `1.3.0` when agents+hooks land (Task 5).

## File Structure

```
skills/clif-icu/scripts/setup_dev_data.sh          modify — --source/--ref/--config flags
skills/clif-icu/scripts/tests/test_setup_dev_data.sh  modify — new cases
skills/clif-icu/reference/synthetic-datasets.md    create — which dataset for which job
skills/clif-icu/SKILL.md                           modify — sandbox sources paragraph
README.md                                          modify — sandbox, hooks, agents, bench sections
hooks/hooks.json                                   create — plugin hook wiring
hooks/phi_guard.py                                 create — PreToolUse blocker
hooks/phi_scan.py                                  create — PostToolUse advisory scanner
hooks/tests/test_phi_hooks.py                      create — pytest, network-free
agents/clif-buddy-tester.md                        create — migrated from ~/.claude/agents/
agents/clif-phi-auditor.md                         create
agents/clif-code-reviewer.md                       create
.claude-plugin/marketplace.json                    modify — agents + hooks + version
bench/README.md                                    create
bench/pin.json                                     create — clif-forge ref + provenance
bench/setup_bench_data.sh                          create — pinned clone + subset
bench/subset_bench_data.py                         create — deterministic 500-hosp subset
bench/conftest.py                                  create — bench_config fixture
bench/harness.py                                   create — solution loader + comparator
bench/generate_truth.py                            create — maintainer-run truth writer
bench/test_bench.py                                create — parametrized runner
bench/tasks/T01_crrt_cohort/{prompt.md,solution.py,expected.json}      create
bench/tasks/T02_imv_cohort/...                     create (same triple, T02–T10)
docs/memo/2026-08-consortium-ai-strategy.md        create — draft
```

---

### Task 1: Sandbox `--source` support

**Files:**
- Modify: `skills/clif-icu/scripts/setup_dev_data.sh`
- Test: `skills/clif-icu/scripts/tests/test_setup_dev_data.sh`

**Interfaces:**
- Produces: `setup_dev_data.sh [--source synthetic-clif|clif-forge-sample|clif-forge-generate] [--ref REF] [--config PATH] [DEST_DIR] [N]`. Exit 0 = sandbox ready (data present + config written); exit 2 otherwise. `clif-forge-sample` copies `sample_dataset/clif_*.parquet` into DEST_DIR — no pip install, no generation. Bench (Task 7) calls this with `--source clif-forge-sample --ref <pin> --config <path>`.

- [ ] **Step 1: Verify clif-forge tag contents and CLI (ground truth, not memory)**

```bash
git -C /Users/kavenchhikara/Projects/CLIF/clif-forge ls-tree --name-only v0.2.0 | head
git -C /Users/kavenchhikara/Projects/CLIF/clif-forge ls-tree --name-only v0.2.0 sample_dataset/ | head
```

Expected: `sample_dataset/` present at `v0.2.0` with `clif_*.parquet` files. If NOT: use `git -C ... rev-parse main` and use that SHA as the pin everywhere `v0.2.0` appears in this plan. Record outcome for Task 7's `pin.json`.

- [ ] **Step 2: Write failing tests for the new flags**

Append to `scripts/tests/test_setup_dev_data.sh`, following its existing stub pattern (STUB_* env toggles; `run_case` style if present — match the file's local helpers). New cases:

```bash
# --- case: unknown --source fails fast, before any clone -------------------
out="$(cd "$WORKDIR" && "$SCRIPT" --source not-a-source 2>&1)"; rc=$?
[ $rc -eq 2 ] && echo "$out" | grep -q "unknown --source" \
  || { echo "FAIL: unknown --source (rc=$rc)"; fails=$((fails+1)); }

# --- case: clif-forge-sample copies committed parquet, no generation -------
# git stub: clone creates DIR/sample_dataset/clif_vitals.parquet + .git
export STUB_GIT_MAKE_SAMPLE=1
out="$(cd "$WORKDIR" && "$SCRIPT" --source clif-forge-sample ./dev_data 2>&1)"; rc=$?
[ $rc -eq 0 ] && [ -f "$WORKDIR/dev_data/clif_vitals.parquet" ] \
  && echo "$out" | grep -q "sandbox ready" \
  || { echo "FAIL: clif-forge-sample happy path (rc=$rc)"; fails=$((fails+1)); }

# --- case: clif-forge-sample with EMPTY sample dir never says ready --------
export STUB_GIT_MAKE_SAMPLE=0
out="$(cd "$WORKDIR2" && "$SCRIPT" --source clif-forge-sample ./dev_data 2>&1)"; rc=$?
[ $rc -eq 2 ] || { echo "FAIL: empty sample must exit 2 (rc=$rc)"; fails=$((fails+1)); }

# --- case: --config writes config at the given path ------------------------
out="$(cd "$WORKDIR3" && "$SCRIPT" --source clif-forge-sample --config ./custom.json ./dev_data 2>&1)"
[ -f "$WORKDIR3/custom.json" ] || { echo "FAIL: --config path"; fails=$((fails+1)); }
```

Extend the git stub's `clone` branch: when `STUB_GIT_MAKE_SAMPLE=1`, also `mkdir -p "$3/sample_dataset" && echo x > "$3/sample_dataset/clif_vitals.parquet"`.

- [ ] **Step 3: Run tests, verify the new cases fail**

Run: `skills/clif-icu/scripts/tests/test_setup_dev_data.sh`
Expected: existing cases PASS, new cases FAIL (script doesn't know `--source` yet — it treats it as DEST_DIR).

- [ ] **Step 4: Implement flag parsing + clif-forge sources**

In `setup_dev_data.sh`, insert flag parsing after `set -euo pipefail` and before the current positional assignment:

```bash
SOURCE="synthetic-clif"; REF_OVERRIDE=""; CONFIG_OVERRIDE=""; POS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --source) SOURCE="$2"; shift 2 ;;
    --ref)    REF_OVERRIDE="$2"; shift 2 ;;
    --config) CONFIG_OVERRIDE="$2"; shift 2 ;;
    -*) echo "error: unknown flag '$1' (see header comment for usage)" >&2; exit 2 ;;
    *) POS+=("$1"); shift ;;
  esac
done
set -- "${POS[@]+"${POS[@]}"}"
case "$SOURCE" in
  synthetic-clif|clif-forge-sample|clif-forge-generate) ;;
  *) echo "error: unknown --source '$SOURCE' (want synthetic-clif | clif-forge-sample | clif-forge-generate)" >&2; exit 2 ;;
esac
```

Then: `CONFIG_PATH="${CONFIG_OVERRIDE:-./clif_demo_config.json}"`. Source-specific vars:

```bash
if [ "$SOURCE" = "synthetic-clif" ]; then
  REPO_URL="https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif"
  CLONE_DIR="./synthetic_clif"; PIN_REF="${REF_OVERRIDE:-${CLIF_SYNTHETIC_REF:-v0.7.0}}"
else
  REPO_URL="https://github.com/sajor2000/clif-forge"
  CLONE_DIR="./clif-forge"; PIN_REF="${REF_OVERRIDE:-${CLIF_FORGE_REF:-v0.2.0}}"
fi
```

Keep the existing clone/fetch/checkout/resolve-SHA block unchanged (it already works off `REPO_URL`/`CLONE_DIR`/`SYNTHETIC_REF` — rename that var to `PIN_REF` throughout). Replace step 2–3 (install + generate) with a source dispatch:

```bash
generated=0
case "$SOURCE" in
  synthetic-clif)
    "$PY" -m pip install -e "$CLONE_DIR"
    if "$PY" -m synthetic_clif --hospitalizations "$N_HOSP" --output "$DEST_DIR" \
            --format parquet --seed 42; then generated=1; fi ;;
  clif-forge-sample)
    if ls "$CLONE_DIR"/sample_dataset/clif_*.parquet >/dev/null 2>&1; then
      mkdir -p "$DEST_DIR"; cp "$CLONE_DIR"/sample_dataset/clif_*.parquet "$DEST_DIR"/
      # keep manifest for provenance if present
      [ -f "$CLONE_DIR/sample_dataset/manifest.json" ] && cp "$CLONE_DIR/sample_dataset/manifest.json" "$DEST_DIR"/
      generated=1
    else
      echo "NOTE: no sample_dataset/clif_*.parquet found in $CLONE_DIR at $PIN_REF." >&2
    fi ;;
  clif-forge-generate)
    "$PY" -m pip install -e "$CLONE_DIR"
    # CLI verified against clif-forge README (Quickstart). Ground-truth check: clif-forge --help
    if clif-forge generate --preset high-acuity --n-patients "$N_HOSP" --out "$DEST_DIR"; then
      generated=1
    else
      echo "NOTE: clif-forge generate failed; check flags with: clif-forge --help" >&2
    fi ;;
esac
```

The clifpy preflight must stay **before** the clone for all sources (fail-fast contract). The final ready/not-ready banner block is unchanged (it keys off `$generated` + non-empty `$DEST_DIR`); update the "Generated from" line to print `$SOURCE @ $PIN_REF ($RESOLVED_SHA)`. Update the header comment usage block for the three flags.

- [ ] **Step 5: Run all tests, verify pass**

Run: `skills/clif-icu/scripts/tests/test_setup_dev_data.sh`
Expected: exit 0, all cases (old + new) PASS.

- [ ] **Step 6: Live smoke test (network) of the fastest path**

```bash
cd "$(mktemp -d)" && /Users/kavenchhikara/Projects/CLIF/skills/skills/clif-icu/scripts/setup_dev_data.sh --source clif-forge-sample ./dev_data
python3 -c "import pandas as pd; df = pd.read_parquet('./dev_data/clif_vitals.parquet'); print(len(df), 'vitals rows')"
```

Expected: "sandbox ready" banner, non-zero row count.

- [ ] **Step 7: Commit**

```bash
git add skills/clif-icu/scripts/setup_dev_data.sh skills/clif-icu/scripts/tests/test_setup_dev_data.sh
git commit -m "feat(sandbox): multi-source dev data via --source (synthetic-clif | clif-forge-sample | clif-forge-generate)"
```

---

### Task 2: "Which synthetic dataset" reference page

**Files:**
- Create: `skills/clif-icu/reference/synthetic-datasets.md`
- Modify: `skills/clif-icu/SKILL.md` (the "Non-PHI dev data" paragraph), `README.md` (PHI-Safe section)

**Interfaces:**
- Produces: a reference doc other tasks link to as `reference/synthetic-datasets.md`.

- [ ] **Step 1: Write the reference page**

Content (write in full, this is the substance):

```markdown
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

**Rules of thumb**
- Agent-assisted development, demos, CI: `clif-forge-sample` (fastest, redistributable) or `synthetic_clif`.
- Statistical realism (model prototyping, plausibility checks): `clif-forge` (calibrated) — still synthetic; never publish inferences from it.
- Validating against real-world messiness: MIMIC-IV-Ext-CLIF — but treat as restricted data; see the BAA/channel rules in phi-safe-development.md before letting ANY agent see it.
- clif-bench pins `clif-forge-sample` for ground truth (see bench/pin.json).

One command for each (from scripts/):
    setup_dev_data.sh --source clif-forge-sample ./dev_data     # fastest
    setup_dev_data.sh --source synthetic-clif ./dev_data 100    # 28 tables, generated
    setup_dev_data.sh --source clif-forge-generate ./dev_data 500  # custom recipe
```

Add pins, upstream URLs, and a "verified 2026-07-31, re-check tags before relying" note.

- [ ] **Step 2: Link it from SKILL.md and README.md**

In `SKILL.md`, extend the "Non-PHI dev data" paragraph: add clif-forge alongside synthetic_clif and link `reference/synthetic-datasets.md`. In `README.md` PHI-Safe section, update the `setup_dev_data.sh` sentence to mention `--source` and the fastest path.

- [ ] **Step 3: Verify links resolve**

Run: `ls skills/clif-icu/reference/synthetic-datasets.md && grep -l "synthetic-datasets.md" skills/clif-icu/SKILL.md README.md`
Expected: all three paths print.

- [ ] **Step 4: Commit**

```bash
git add skills/clif-icu/reference/synthetic-datasets.md skills/clif-icu/SKILL.md README.md
git commit -m "docs: synthetic dataset chooser (synthetic_clif vs clif-forge vs MIMIC-CLIF)"
```

---

### Task 3: PHI guard hook (PreToolUse blocker)

**Files:**
- Create: `hooks/phi_guard.py`
- Test: `hooks/tests/test_phi_hooks.py`

**Interfaces:**
- Consumes: hook stdin JSON `{"tool_name": str, "tool_input": {...}}` (Claude Code PreToolUse contract).
- Produces: exit 0 = allow; exit 2 + stderr message = block. Config: newline-delimited PHI directory paths, `#` comments, from the first-existing union of `$CLIF_PHI_PATHS_FILE`, `./.clif-phi-paths`, `~/.clif/phi-paths`. Task 4 reuses `load_phi_paths()` and `TEXT_KEYS`; Task 5 wires it into `hooks.json`.

- [ ] **Step 1: Write failing tests**

`hooks/tests/test_phi_hooks.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python3 -m pytest hooks/tests/test_phi_hooks.py -v`
Expected: FAIL / errors — `phi_guard.py` doesn't exist.

- [ ] **Step 3: Implement `hooks/phi_guard.py`**

```python
#!/usr/bin/env python3
"""clif-icu PHI guard (PreToolUse).

Blocks agent tool access to real-data directories the site lists in a config
file. Mechanical enforcement of the PHI-safe workflow in
skills/clif-icu/reference/phi-safe-development.md.

Config: newline-delimited directory paths ('#' comments allowed) from ALL of:
  $CLIF_PHI_PATHS_FILE, ./.clif-phi-paths, ~/.clif/phi-paths  (union of those
  that exist). No config => allow everything (guard inactive until configured).

Contract: exit 0 allow; exit 2 block (stderr shown to the agent). Stdlib only.
"""
import json, os, sys

PATH_KEYS = ("file_path", "path", "notebook_path")
TEXT_KEYS = ("command",)  # Bash


def config_sources():
    return [os.environ.get("CLIF_PHI_PATHS_FILE"),
            os.path.join(os.getcwd(), ".clif-phi-paths"),
            os.path.expanduser("~/.clif/phi-paths")]


def load_phi_paths():
    """Return [(raw_line, realpath)] for every configured PHI dir."""
    out = []
    for src in config_sources():
        if not src or not os.path.isfile(src):
            continue
        try:
            with open(src) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        out.append((line, os.path.realpath(os.path.expanduser(line))))
        except OSError:
            continue
    return out


def is_under(target, root):
    t = os.path.realpath(os.path.expanduser(target))
    return t == root or t.startswith(root + os.sep)


def block(value, raw):
    sys.stderr.write(
        f"BLOCKED by clif-icu PHI guard: '{value}' is inside the configured "
        f"real-data path '{raw}'. Agents must never receive PHI. Use the "
        "non-PHI sandbox (skills/clif-icu/scripts/setup_dev_data.sh); see "
        "reference/phi-safe-development.md. To change guarded paths, edit "
        "the PHI paths config (.clif-phi-paths / ~/.clif/phi-paths).\n")
    return 2


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # malformed input: never break the session
    tool_input = data.get("tool_input") or {}
    phi = load_phi_paths()
    if not phi:
        return 0
    for key in PATH_KEYS:
        v = tool_input.get(key)
        if isinstance(v, str):
            for raw, root in phi:
                if is_under(v, root):
                    return block(v, raw)
    for key in TEXT_KEYS:
        v = tool_input.get(key)
        if isinstance(v, str):
            for raw, root in phi:
                # conservative substring check on command text, raw + resolved
                if raw in v or root in v:
                    return block(key + ": " + v[:120], raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`chmod +x hooks/phi_guard.py`.

- [ ] **Step 4: Run tests, verify pass**

Run: `python3 -m pytest hooks/tests/test_phi_hooks.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add hooks/phi_guard.py hooks/tests/test_phi_hooks.py
git commit -m "feat(hooks): PreToolUse PHI guard blocks configured real-data paths"
```

---

### Task 4: PHI scan hook (PostToolUse advisory)

**Files:**
- Create: `hooks/phi_scan.py`
- Test: `hooks/tests/test_phi_hooks.py` (append)

**Interfaces:**
- Consumes: PostToolUse stdin JSON `{"tool_name", "tool_input", "tool_response"}`; reuses `phi_guard.load_phi_paths` semantics for its off-switch only (independent module, no import between hooks — duplicate the 3-line env check instead).
- Produces: exit 0 always; on suspicious output, prints JSON `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "<warning>"}}` so the agent is told to stop and sanitize. `CLIF_PHI_SCAN=off` disables.

- [ ] **Step 1: Append failing tests**

```python
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
```

- [ ] **Step 2: Run, verify the new tests fail**

Run: `python3 -m pytest hooks/tests/test_phi_hooks.py -v -k scan`
Expected: FAIL — `phi_scan.py` missing.

- [ ] **Step 3: Implement `hooks/phi_scan.py`**

```python
#!/usr/bin/env python3
"""clif-icu PHI output scanner (PostToolUse). ADVISORY, never blocks.

Flags PHI-shaped patterns in tool output so the agent stops and sanitizes.
Synthetic data triggers false positives by design — the warning says how to
proceed if the data is confirmed non-PHI. CLIF_PHI_SCAN=off disables.
Exit 0 always. Stdlib only.
"""
import json, os, re, sys

PATTERNS = [
    ("MRN-like identifier", re.compile(r"\bMRN\W{0,3}\d{5,}", re.I)),
    ("SSN-like number",     re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("DOB-like field",      re.compile(r"\bDOB\W{0,3}(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})", re.I)),
    ("birth-date-like value", re.compile(r"\b(?:19[0-9]{2}|20[0-4][0-9])-\d{2}-\d{2}\b.{0,20}\b(?:birth|dob)\b|\b(?:birth|dob)\b.{0,20}\b(?:19[0-9]{2}|20[0-4][0-9])-\d{2}-\d{2}\b", re.I)),
]


def response_text(resp):
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        return " ".join(str(v) for v in resp.values() if isinstance(v, (str, int, float)))
    return ""


def main():
    if os.environ.get("CLIF_PHI_SCAN", "").lower() == "off":
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    text = response_text(data.get("tool_response"))[:200_000]
    hits = sorted({label for label, rx in PATTERNS if rx.search(text)})
    if hits:
        warning = (
            "clif-icu PHI scan: tool output contains PHI-shaped patterns ("
            + ", ".join(hits) + "). STOP: do not repeat, summarize, or reason "
            "over these values. If this is real data, the PHI-safe workflow has "
            "been violated — tell the user to open a NEW session against the "
            "non-PHI sandbox (reference/phi-safe-development.md). If the data "
            "is confirmed synthetic (e.g. the sandbox from setup_dev_data.sh), "
            "say so explicitly and continue.")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": warning}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`chmod +x hooks/phi_scan.py`.

- [ ] **Step 4: Run all hook tests, verify pass**

Run: `python3 -m pytest hooks/tests/test_phi_hooks.py -v`
Expected: all PASS (guard + scan).

- [ ] **Step 5: Commit**

```bash
git add hooks/phi_scan.py hooks/tests/test_phi_hooks.py
git commit -m "feat(hooks): PostToolUse advisory scanner for PHI-shaped output"
```

---

### Task 5: Plugin packaging — hooks.json, agents/, manifest

**Files:**
- Create: `hooks/hooks.json`, `agents/clif-buddy-tester.md`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: `hooks/phi_guard.py`, `hooks/phi_scan.py` (Tasks 3–4).
- Produces: plugin v1.3.0 that installs skill + hooks + agents together. Task 6 adds two more files to `agents/`.

- [ ] **Step 1: Write `hooks/hooks.json`**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Glob|Grep|Bash|Edit|Write|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/phi_guard.py\""}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Read|Bash",
        "hooks": [
          {"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/phi_scan.py\""}
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Migrate the buddy tester**

```bash
mkdir -p agents && cp /Users/kavenchhikara/.claude/agents/clif-buddy-tester.md agents/clif-buddy-tester.md
```

Then edit `agents/clif-buddy-tester.md`: no content changes except — verify the frontmatter has `name`, `description`, `tools: Read, Grep, Glob, Bash` (it does), and add one line at the end of the description noting it ships with the clif-icu plugin.

- [ ] **Step 3: Wire the manifest**

`.claude-plugin/marketplace.json` — update the plugin entry and version:

```json
{
  "name": "clif-skills",
  "owner": {"name": "CLIF Consortium - VC", "email": "clif_consortium@uchicago.edu"},
  "metadata": {
    "description": "CLIF ICU data format and clifpy Python library skills",
    "version": "1.3.0"
  },
  "plugins": [
    {
      "name": "clif-icu",
      "description": "Analyzes ICU clinical data using CLIF format and clifpy. Loads tables, computes SOFA/CCI/Elixhauser scores, creates wide datasets. Ships PHI guardrail hooks and consortium agents (buddy-tester, phi-auditor, code-reviewer).",
      "source": "./",
      "strict": false,
      "skills": ["./skills/clif-icu"],
      "agents": ["./agents"],
      "hooks": "./hooks/hooks.json"
    }
  ]
}
```

- [ ] **Step 4: Validate the plugin loads**

Run: `claude plugin validate . 2>&1 || true` — if the subcommand exists, expect "valid". Regardless, do a live check: in a scratch dir, `claude --plugin-dir /Users/kavenchhikara/Projects/CLIF/skills` (or install from the local marketplace path), then `/agents` must list clif-buddy-tester and `/hooks` must show the two PHI hooks. Record actual output in the task notes; if the manifest keys for agents/hooks are rejected, check `claude plugin --help` / official plugin-schema docs and adjust key names — do not guess silently.

- [ ] **Step 5: Manual hook verification (the demo that matters for the memo)**

In that scratch session with the plugin loaded: `echo "/tmp/fake_phi" > .clif-phi-paths`, `mkdir -p /tmp/fake_phi && echo "x" > /tmp/fake_phi/labs.csv`, then ask Claude to read `/tmp/fake_phi/labs.csv`.
Expected: read is BLOCKED with the PHI-guard message. Screenshot/copy the transcript line for the memo.

- [ ] **Step 6: Commit**

```bash
git add hooks/hooks.json agents/clif-buddy-tester.md .claude-plugin/marketplace.json
git commit -m "feat(plugin): ship PHI hooks and buddy-tester agent with the plugin (v1.3.0)"
```

---

### Task 6: clif-phi-auditor + clif-code-reviewer agents

**Files:**
- Create: `agents/clif-phi-auditor.md`, `agents/clif-code-reviewer.md`

**Interfaces:**
- Consumes: agent frontmatter conventions from `agents/clif-buddy-tester.md` (Task 5).
- Produces: two read-only agents installed with the plugin.

- [ ] **Step 1: Write `agents/clif-phi-auditor.md`**

```markdown
---
name: clif-phi-auditor
description: Use before sharing, pushing, or distributing ANY CLIF artifact — a repo, results tables, figures, logs, or a study-kit output bundle — to scan it for PHI leakage and small-cell risk. Also use when asked "is this safe to share?". Reports evidence-backed findings with file:line cites; the human makes the final share/no-share call.
tools: Read, Grep, Glob, Bash
---

You are the PHI pre-flight auditor for CLIF artifacts. Your job: find anything in the
target directory that could leak PHI or re-identifiable information BEFORE it leaves
the site. You are read-only — never modify or delete; report.

## What to scan for (all of these, every time)

1. **Direct identifiers in files**: MRN-like numbers, SSNs, names next to clinical
   values, DOBs, full dates of service tied to a patient, addresses, phone numbers.
   Grep patterns to start from (extend, don't stop here):
   `MRN`, `\b\d{3}-\d{2}-\d{4}\b`, `dob|birth`, `patient_name|first_name|last_name`.
2. **Row-level data where aggregates were promised**: any CSV/parquet in an output/
   results dir with one-row-per-patient/hospitalization granularity, `.head()` dumps
   in logs or notebooks, example rows pasted into READMEs or comments.
3. **Small cells**: any released count < 11 in tables/figures (report the site's
   threshold as unknown — surface, don't decide). Check totals AND subgroup cells,
   including complements (a suppressed cell recoverable by subtraction).
4. **Identifier columns in outputs**: `patient_id`, `hospitalization_id`, encounter
   keys, bed/room identifiers — even hashed ones if the hash is site-reversible.
5. **Hardcoded site paths and configs**: real data directories, server names,
   usernames in paths, credentials, `config.json` pointing at non-sandbox data.
6. **Notebook and log residue**: executed notebook outputs, `.log` files, tracebacks
   embedding data values, `__pycache__`/`.parquet` files that shouldn't ship.
7. **Git history**: if the target is a repo, check tracked files AND
   `git log --diff-filter=D --name-only` for previously-committed data files; a
   deleted PHI file still lives in history.

## Hard rules

- Every finding: severity (BLOCKER / WARN / INFO), file path (+line where sensible),
  and the exact evidence. Never report a suspicion you did not confirm.
- NEVER quote the potentially-PHI value itself in your report beyond the minimum
  needed to locate it (e.g. "8-digit number after 'MRN' at results/log.txt:412" —
  not the number).
- Synthetic/sandbox data triggers the same patterns; if provenance says synthetic
  (manifest.json, setup_dev_data.sh sandbox, synthetic_clif/clif-forge paths),
  mark findings INFO with that provenance noted — verify the provenance claim, do
  not take a directory name's word for it.
- You do not decide the suppression threshold, whether a hash is safe, or whether
  something ships. Surface evidence; the human decides.

## Report format

Summary verdict line (SAFE TO SHARE AS-IS is allowed only with zero BLOCKER and
zero WARN), then findings grouped by severity, then the checklist above with a
checked/unchecked status per item so coverage is auditable.
```

- [ ] **Step 2: Write `agents/clif-code-reviewer.md`**

```markdown
---
name: clif-code-reviewer
description: Use to review CLIF analysis code (Python/clifpy, R, SQL, notebooks) before it runs on real data or ships in a study kit — catches the CLIF-specific footguns that produce plausible-but-wrong multi-site results. Also use when CLIF results look implausible and the pipeline needs a correctness audit.
tools: Read, Grep, Glob, Bash
---

You review CLIF analysis code for correctness. The dangerous failure mode in
federated research is code that RUNS CLEAN and returns WRONG numbers that get
pooled across sites. Hunt for that.

## The CLIF footgun list (check every one, in order)

1. **Category value drift (2.1 vs 3.0)**: 2.1 uses e.g. `IMV`, `High Flow NC`;
   3.0 renames to snake_case (`imv`, `hfnc`). A filter written for the wrong
   version silently matches ZERO rows. Check every `*_category` literal against
   the declared schema version (ask which version if undeclared; check
   CLIF_SCHEMA_VERSION). A filter that matches zero rows is a finding, not a shrug.
2. **Case/whitespace-sensitive string filters**: `== "imv"` vs `.str.lower()`,
   trailing spaces, `isin` lists with typos. Verify literals against the mCIDE
   vocab files (skills/clif-icu/mCIDE/) or the table's schema YAML.
3. **Patient vs hospitalization unit errors**: joining patient-level tables
   (patient) to hospitalization-level tables without deduplication; counting
   hospitalizations and calling them patients; encounter stitching ignored or
   double-applied.
4. **Timezone bugs**: naive vs aware datetimes mixed; site timezone not applied;
   comparisons across DST boundaries; `dttm` columns compared to dates.
5. **Unit errors in meds and labs**: medication doses not standardized
   (mcg/kg/min vs mcg/min vs mg/hr) before comparison; lab units differing across
   sites; weight-based dosing without weight join. clifpy has unit conversion —
   flag hand-rolled conversions and verify against it.
6. **Outlier/plausibility handling**: no bounds applied (or bounds applied twice)
   versus the outlier config; physiologically impossible values silently included.
7. **Missing-data semantics**: NaN treated as false/zero in flags; LOCF applied
   to labs where it changes clinical meaning; wide-dataset hourly bins assuming
   complete grids.
8. **Silent try/except**: analysis wrapped in `try/except: continue` that
   converts crashes into missing artifacts. Every except must be visible/logged.
9. **Small-cell discipline**: released outputs missing suppression on n<threshold
   cells (surface the threshold question to the human, don't pick one).
10. **API misuse from memory**: calls to clifpy that don't match its actual
    signatures. Verify with `python3 -c "import inspect; ..."` — never from memory.

## Hard rules

- Evidence per finding: file:line + why it is wrong + concrete failure scenario
  (input → wrong output). No style nits unless they hide a correctness risk.
- Verify claims against the actual schema YAMLs / mCIDE vocab / clifpy signatures
  in this plugin or the installed clifpy — not from memory.
- Never run the code against real data; if execution helps, use the non-PHI
  sandbox (scripts/setup_dev_data.sh).
- Severity: BLOCKER (wrong numbers will pool), WARN (fragile), INFO. End with the
  footgun list, checked off, so coverage is auditable.
```

- [ ] **Step 3: Verify agents load**

In the scratch plugin session (Task 5 step 4 setup): `/agents` lists all three; invoke `clif-phi-auditor` on `bench/` (once it exists — or on `skills/`) as a smoke test and confirm it produces the report format.

- [ ] **Step 4: Commit**

```bash
git add agents/clif-phi-auditor.md agents/clif-code-reviewer.md
git commit -m "feat(agents): PHI pre-flight auditor and CLIF footgun code reviewer"
```

---

### Task 7: clif-bench harness + pilot tasks (T01, T08)

**Files:**
- Create: `bench/README.md`, `bench/pin.json`, `bench/setup_bench_data.sh`, `bench/subset_bench_data.py`, `bench/conftest.py`, `bench/harness.py`, `bench/generate_truth.py`, `bench/test_bench.py`, `bench/tasks/T01_crrt_cohort/{prompt.md,solution.py}`, `bench/tasks/T08_category_trap/{prompt.md,solution.py}`, and their `expected.json` (generated, committed).

**Interfaces:**
- Consumes: `setup_dev_data.sh --source clif-forge-sample --ref <pin> --config <path> <dest>` (Task 1).
- Produces: task contract — `solution.py` defines `solve(config_path: str) -> dict` returning ONLY aggregate values; `expected.json` mirrors that dict; `harness.assert_matches(result, expected)` compares (exact for ints/strings, `rel=1e-4` for floats). `python3 bench/generate_truth.py [TASK_ID ...]` (maintainer-run) writes `expected.json` per task with independent-of-solution code. Task 8 adds T02–T07, T09, T10 to the same contract.

- [ ] **Step 1: Data plumbing — `pin.json`, `setup_bench_data.sh`, `subset_bench_data.py`**

`bench/pin.json` (use the ref verified in Task 1 step 1):

```json
{
  "source": "clif-forge-sample",
  "repo": "https://github.com/sajor2000/clif-forge",
  "ref": "v0.2.0",
  "subset": {"n_hospitalizations": 500, "rule": "first 500 hospitalization_id ascending (numeric sort)"},
  "verified": "2026-07-31"
}
```

`bench/setup_bench_data.sh`:

```bash
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
from clifpy.utils.config import create_example_config
create_example_config(data_directory="./subset", filetype="parquet",
                      timezone="US/Central", output_directory="./output",
                      config_path="./config.json")
PY
echo "bench data ready: bench/.data/config.json"
```

`bench/subset_bench_data.py`:

```python
#!/usr/bin/env python3
"""Deterministic bench subset: first N hospitalization_ids (ascending numeric)."""
import json, shutil, sys
from pathlib import Path
import pandas as pd

def main(src, dst, n=None):
    src, dst = Path(src), Path(dst)
    n = n or json.load(open(Path(__file__).parent / "pin.json"))["subset"]["n_hospitalizations"]
    dst.mkdir(parents=True, exist_ok=True)
    hosp = pd.read_parquet(src / "clif_hospitalization.parquet")
    ids = hosp["hospitalization_id"].drop_duplicates().sort_values(
        key=lambda s: pd.to_numeric(s, errors="coerce")).head(n)
    keep_h = set(ids)
    keep_p = set(hosp[hosp.hospitalization_id.isin(keep_h)]["patient_id"])
    for f in sorted(src.glob("clif_*.parquet")):
        df = pd.read_parquet(f)
        if "hospitalization_id" in df.columns:
            df = df[df.hospitalization_id.isin(keep_h)]
        elif "patient_id" in df.columns:
            df = df[df.patient_id.isin(keep_p)]
        # tables keyed some other way (e.g. provider): keep whole
        df.to_parquet(dst / f.name, index=False)
    print(f"subset: {len(keep_h)} hospitalizations, {len(keep_p)} patients -> {dst}")

if __name__ == "__main__":
    main(*sys.argv[1:3])
```

Add `bench/.data/` to `.gitignore`.

- [ ] **Step 2: Harness — `harness.py`, `conftest.py`, `test_bench.py`**

`bench/harness.py`:

```python
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
        assert set(result) == set(expected), f"{path}: keys {set(result)} != {set(expected)}"
        for k in expected:
            assert_matches(result[k], expected[k], f"{path}.{k}")
    elif isinstance(expected, list):
        assert len(result) == len(expected), f"{path}: length"
        for i, (r, e) in enumerate(zip(result, expected)):
            assert_matches(r, e, f"{path}[{i}]")
    elif isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4), f"{path}"
    else:
        assert result == expected, f"{path}: {result!r} != {expected!r}"
```

`bench/conftest.py`:

```python
import json
from pathlib import Path
import pytest

@pytest.fixture(scope="session")
def bench_config():
    cfg = Path(__file__).parent / ".data" / "config.json"
    if not cfg.exists():
        pytest.skip("bench data missing — run bench/setup_bench_data.sh first")
    return str(cfg)
```

`bench/test_bench.py`:

```python
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
```

- [ ] **Step 3: Run pytest, verify the harness fails for the right reason**

Run: `cd bench && python3 -m pytest test_bench.py -v`
Expected: collection succeeds; zero tasks collected (no task dirs yet) or skip on missing data — no import errors.

- [ ] **Step 4: Pilot tasks T01 + T08**

`bench/tasks/T01_crrt_cohort/prompt.md`:

```markdown
# T01: CRRT cohort size
Using the CLIF dataset at the config path you are given (clifpy-compatible
config.json), identify the CRRT cohort: every hospitalization that appears in
the crrt_therapy table. Write `solution.py` with
`solve(config_path: str) -> dict` returning:
{"n_crrt_hospitalizations": <int>, "pct_of_all_hospitalizations": <float 0-100, 2dp>}
Aggregates only — never return row-level records or ID lists.
```

`bench/tasks/T01_crrt_cohort/solution.py` (reference solution — also a worked example for the skill):

```python
import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    crrt = pd.read_parquet(data_dir / "clif_crrt_therapy.parquet",
                           columns=["hospitalization_id"])
    hosp = pd.read_parquet(data_dir / "clif_hospitalization.parquet",
                           columns=["hospitalization_id"])
    n = crrt.hospitalization_id.nunique()
    return {"n_crrt_hospitalizations": int(n),
            "pct_of_all_hospitalizations": round(100 * n / hosp.hospitalization_id.nunique(), 2)}
```

(Config key name `data_directory`: verify against the config Task 1 writes — `python3 -c "import json;print(json.load(open('bench/.data/config.json')))"` — and adjust if clifpy names it differently.)

`bench/tasks/T08_category_trap/prompt.md`:

```markdown
# T08: High-flow nasal cannula usage (category-convention trap)
This dataset is CLIF **2.1**. Count hospitalizations with any high-flow
nasal cannula support recorded in respiratory_support, and separately any
invasive mechanical ventilation. Return
{"n_hfnc_hospitalizations": <int>, "n_imv_hospitalizations": <int>}.
Aggregates only. (Scoring note, not shown to agents: 2.1 uses
`High Flow NC` / `IMV`; an agent using 3.0's `hfnc` / `imv` scores zero.)
```

`bench/tasks/T08_category_trap/solution.py`:

```python
import json
import pandas as pd
from pathlib import Path

def solve(config_path: str) -> dict:
    data_dir = Path(json.load(open(config_path))["data_directory"])
    rs = pd.read_parquet(data_dir / "clif_respiratory_support.parquet",
                         columns=["hospitalization_id", "device_category"])
    def n_with(cat):
        return int(rs.loc[rs.device_category == cat, "hospitalization_id"].nunique())
    return {"n_hfnc_hospitalizations": n_with("High Flow NC"),
            "n_imv_hospitalizations": n_with("IMV")}
```

Before committing: verify the actual 2.1 category literals in the sample —
`python3 -c "import pandas as pd; print(pd.read_parquet('bench/.data/subset/clif_respiratory_support.parquet', columns=['device_category']).device_category.value_counts())"` — and against `skills/clif-icu/schemas/respiratory_support_schema.yaml`. If the dataset uses different literals, fix BOTH the solution and the prompt's scoring note to the schema-true values.

- [ ] **Step 5: `generate_truth.py` (independent computation, duckdb-free stdlib+pandas)**

```python
#!/usr/bin/env python3
"""Maintainer-run: compute ground truth for bench tasks and write expected.json.

Truth code is written INDEPENDENTLY of the reference solutions (different
implementation where feasible) so a shared bug can't self-confirm.
Usage: python3 generate_truth.py [T01 T08 ...]   (default: all known)
"""
import json, sys
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / ".data" / "subset"
TASKS = Path(__file__).parent / "tasks"

def _pq(name, cols=None):
    return pd.read_parquet(DATA / f"clif_{name}.parquet", columns=cols)

def truth_T01_crrt_cohort():
    ids_crrt = set(_pq("crrt_therapy", ["hospitalization_id"]).hospitalization_id)
    ids_all = set(_pq("hospitalization", ["hospitalization_id"]).hospitalization_id)
    return {"n_crrt_hospitalizations": len(ids_crrt & ids_all) if ids_crrt <= ids_all else len(ids_crrt),
            "pct_of_all_hospitalizations": round(100 * len(ids_crrt) / len(ids_all), 2)}

def truth_T08_category_trap():
    rs = _pq("respiratory_support", ["hospitalization_id", "device_category"])
    by = rs.groupby("device_category")["hospitalization_id"].nunique()
    return {"n_hfnc_hospitalizations": int(by.get("High Flow NC", 0)),
            "n_imv_hospitalizations": int(by.get("IMV", 0))}

TRUTH = {name.split("truth_")[1]: fn for name, fn in list(globals().items())
         if name.startswith("truth_")}

def main(only=None):
    for task_id_name, fn in sorted(TRUTH.items()):
        tid = task_id_name.split("_")[0]
        if only and tid not in only:
            continue
        out = TASKS / task_id_name / "expected.json"
        out.write_text(json.dumps(fn(), indent=2) + "\n")
        print(f"wrote {out}")

if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
```

Cross-check T08 truth against clif-forge's own `clif_truth.parquet` where semantics align (e.g. `resp_flag`) — note agreement/disagreement in `bench/README.md`; disagreement is a finding to raise with JC, not something to paper over.

- [ ] **Step 6: Generate data + truth, run the bench green**

```bash
bash bench/setup_bench_data.sh
python3 bench/generate_truth.py
cd bench && python3 -m pytest test_bench.py -v
```

Expected: T01 and T08 PASS. If a reference solution disagrees with truth, debug — the two were written independently, so a mismatch means one has a real bug.

- [ ] **Step 7: `bench/README.md`**

Write: what clif-bench is (CI for the skill + citable correctness benchmark + extensible template), the task contract (`solve(config_path) -> dict`, aggregates only), how to run (3 commands from step 6), how to score an agent (give it only `prompt.md` + the config path; drop its `solution.py` into the task dir; run pytest; report N-passed / N-total for skill-assisted vs raw), the pin/provenance story (pin.json + clif-forge manifest SHA256s), and how a site adds a task (copy a task dir, add a `truth_TXX_*` function, regenerate).

- [ ] **Step 8: Commit**

```bash
git add bench/ .gitignore
git commit -m "feat(bench): clif-bench v0 harness with pinned clif-forge data and pilot tasks T01, T08"
```

---

### Task 8: Bench tasks T02–T07, T09, T10

**Files:**
- Create: `bench/tasks/T0X_*/{prompt.md,solution.py,expected.json}` for the eight below; append `truth_*` functions to `bench/generate_truth.py`.

**Interfaces:**
- Consumes: Task 7's contract exactly (`solve(config_path) -> dict`, `truth_TXX_name()` naming, `assert_matches` tolerances).

- [ ] **Step 1: Verify clifpy APIs before writing clifpy-backed tasks (T05–T07)**

```bash
python3 - <<'PY'
import inspect
from clifpy import ClifOrchestrator
print(inspect.signature(ClifOrchestrator.__init__))
for name in dir(ClifOrchestrator):
    if any(k in name.lower() for k in ("sofa", "wide", "convert", "unit")):
        print(name)
PY
```

Record actual names/signatures; use ONLY those in the solutions below (adjust call syntax to reality — the task definitions below fix the *semantics* and the *output dict*, not the exact clifpy call).

- [ ] **Step 2: Implement the eight tasks.** For each: prompt.md states the question + exact return dict; solution.py is the reference implementation; truth function computes independently (pandas where the solution uses clifpy, and vice versa where feasible). Definitions:

| ID | Question | Return dict | Truth approach |
|---|---|---|---|
| T02_imv_cohort | N hospitalizations ever on invasive mechanical ventilation | `{"n_imv_hospitalizations": int}` | pandas groupby on respiratory_support device_category (schema-true literal) |
| T03_mortality | In-hospital mortality | `{"n_expired": int, "mortality_pct": float2dp}` | pandas on hospitalization discharge_category — verify the literal (`Expired` vs other) against `hospitalization_schema.yaml` and the actual data first |
| T04_icu_los | Median ICU length-of-stay in hours (per ICU stay interval in adt, location_category ICU-valued) | `{"n_icu_stays": int, "median_icu_los_hours": float2dp}` | pandas: `(out_dttm - in_dttm)` per ICU row; verify adt column names against `adt_schema.yaml` |
| T05_norepi_dose | Among hospitalizations receiving norepinephrine (med_category per mCIDE), median of per-hospitalization max standardized dose (mcg/kg/min) | `{"n_norepi_hospitalizations": int, "median_peak_dose_mcg_kg_min": float2dp}` | solution uses clifpy unit conversion; truth hand-computes from med_dose/med_dose_unit + weight — where units in sample are uniform this is trivial; if hand-conversion proves error-prone, truth = independently-written clifpy call path, noted in README |
| T06_day1_sofa | Mean day-1 SOFA total across first 100 subset hospitalization_ids (ascending numeric) | `{"n_scored": int, "mean_day1_sofa": float2dp}` | truth = clifpy compute at PINNED clifpy version (record version in expected.json as `"_clifpy_version"`; harness ignores keys starting with `_` — add that to `assert_matches`) — this task locks regression behavior rather than independent truth; say so in README |
| T07_hourly_wide | Hourly wide dataset for heart_rate over first 20 subset hospitalizations: rows and global mean | `{"n_rows": int, "mean_heart_rate": float2dp}` | solution uses clifpy wide-dataset API; truth: pandas floor-to-hour groupby mean on vitals — if clifpy's binning differs (label left/right), reconcile deliberately and document the chosen semantic in prompt.md so agents aren't guessing |
| T09_small_cell | Race × sex count table with cells n<11 suppressed | `{"n_cells_total": int, "n_cells_suppressed": int, "n_reported": int}` (n_reported = sum of unsuppressed cells) | pandas crosstab on patient table; literals from `patient_schema.yaml` |
| T10_potassium_outliers | N potassium lab values outside the outlier config's plausible range | `{"n_potassium_values": int, "n_outside_range": int}` | bounds read from `skills/clif-icu/schemas/outlier_config.yaml` (parse with `yaml` if available else regex the two numbers); lab_category literal verified against data + `labs_schema.yaml` |

Every prompt.md ends with: "Aggregates only — never return row-level records or ID lists."

- [ ] **Step 3: Generate truth, run full bench**

```bash
python3 bench/generate_truth.py && cd bench && python3 -m pytest test_bench.py -v
```

Expected: 10/10 PASS. Debug any truth-vs-solution mismatch to root cause (independent implementations disagreeing = real bug somewhere; find which).

- [ ] **Step 4: Sanity-check plausibility of committed truths**

Read every `expected.json`; flag absurdities (0 CRRT patients, 100% mortality, negative LOS) against clif-forge's manifest illness-rate spec (`imv: 0.28`, `crrt_prob: 0.29`, `mortality_scale`) — if T02's IMV fraction is wildly off ~28% of hospitalizations, investigate before committing.

- [ ] **Step 5: Commit**

```bash
git add bench/
git commit -m "feat(bench): tasks T02-T10 — cohorts, mortality, LOS, doses, SOFA, wide, suppression, outliers"
```

---

### Task 9: Strategy memo draft + README surface

**Files:**
- Create: `docs/memo/2026-08-consortium-ai-strategy.md`
- Modify: `README.md` (add Agents, Hooks, clif-bench sections to the feature table/structure diagram)

**Interfaces:**
- Consumes: artifacts + evidence from Tasks 1–8 (hook-block transcript from Task 5 step 5, bench task count, sandbox one-liners).

- [ ] **Step 1: Write the memo draft** — leadership memo (~2 pages) + technical appendix. Required structure and claims (flesh each bullet into prose; cite only artifacts that exist):

```markdown
# AI for CLIF Research: Consortium Strategy — DRAFT for review
(To: site PIs and technical leads. From: CLIF tech team. 2026-08)

## The problem (3 short paragraphs)
- Sites want AI assistance; PHI uncertainty blocks some entirely, and
  plausible-but-wrong AI-written CLIF code threatens pooled results.
- Every site improvising separately = fragmented, unreviewable practice.

## What we built (the trust layer) — each with one evidence line
- Mechanical PHI guardrails: the tool CANNOT read configured real-data paths
  (hook-block transcript excerpt). Instructions became enforcement.
- Two-phase workflow + one-command non-PHI sandbox (two consortium synthetic
  datasets: synthetic_clif, CLIFForge — clone-and-go).
- clif-bench: 10 golden tasks, ground truth precomputed; how sites/models score.
- Consortium agents: buddy-tester, phi-auditor, code-reviewer — installed with
  the plugin, same review discipline at every site.

## What we recommend sites do now (checklist, one install command)

## Honest limits
- Hooks are Claude Code-only today; other tools get the skill text + agents
  guidance only (portability matrix coming in phase B).
- Guardrails reduce risk; they are not compliance. IRB/privacy sign-off still
  governs. BAA channel matrix lives in phi-safe-development.md and is perishable.
- clif-bench measures task correctness on synthetic data, not clinical validity.

## Roadmap: A (this memo) → B (portability: cross-tool matrix, project template
  repo) → C (ecosystem: local MCP server, ETL-validator + migration agents)

## Appendix A: the landscape (1 page)
- Agent Skills open standard (SKILL.md) — why we bet on it; MCP — what a local
  server would add in phase C; hooks; evals; synthetic data generators compared
  (link reference/synthetic-datasets.md); BAA channels (link, perishable).
## Appendix B: install + verify (exact commands; the Task 5 hook demo as the
  site-level acceptance test)
```

- [ ] **Step 2: README surface.** Add to `README.md`: an **Agents** table (three agents, one-line each), a **PHI hooks** subsection under PHI-Safe (what's blocked, how to configure `.clif-phi-paths`, the off-switches), a **clif-bench** section (what/run/score), and update the repo-structure diagram with `agents/`, `hooks/`, `bench/`, `docs/memo/`.

- [ ] **Step 3: Self-check the memo against reality** — every claim in the memo must point at a real artifact in this repo at its stated path; fix or cut any that don't.

- [ ] **Step 4: Commit**

```bash
git add docs/memo/2026-08-consortium-ai-strategy.md README.md
git commit -m "docs: consortium AI strategy memo draft; README surface for agents/hooks/bench"
```

---

### Task 10: Integration verification (fresh-clone walkthrough)

**Files:** none created — this is the acceptance gate.

- [ ] **Step 1: Fresh-clone dry run**

```bash
cd "$(mktemp -d)" && git clone /Users/kavenchhikara/Projects/CLIF/skills skills && cd skills
skills/clif-icu/scripts/tests/test_setup_dev_data.sh          # bash tests green
python3 -m pytest hooks/tests/ -v                              # hook tests green
bash bench/setup_bench_data.sh && python3 bench/generate_truth.py
python3 -m pytest bench/test_bench.py -v                       # 10/10 green
```

- [ ] **Step 2: Regenerated truth must match committed truth**

Run: `git status --porcelain bench/tasks/`
Expected: EMPTY — `generate_truth.py` on freshly-pinned data reproduces the committed `expected.json` byte-identically. Any diff = non-determinism or pin drift; find root cause.

- [ ] **Step 3: Plugin walkthrough** — repeat Task 5 steps 4–5 from the fresh clone (agents listed, hook demo blocks). 

- [ ] **Step 4: Design-spec audit** — walk `2026-07-31-005` success criteria one by one against reality; every deliverable and criterion checked off with evidence, per the deliverable-audit rule. Report results to Kaveri with the pass/fail table. **Ask permission before any push/PR.**

---

## Self-Review (completed)

- **Spec coverage:** sandbox (T1–T2), hooks (T3–T5), agents (T5–T6), bench (T7–T8), memo (T9), success criteria (T10). Phase B/C items correctly absent.
- **Placeholders:** none — all code/content inline; the two deliberate verify-against-reality points (clifpy signatures, category literals) are explicit steps with commands, not hand-waves.
- **Type consistency:** `solve(config_path: str) -> dict` and `truth_TXX_name()` used consistently across T7/T8; `assert_matches` tolerance stated once and referenced; `--source/--ref/--config` flag names consistent across T1/T7.
- **Note for executors:** `assert_matches` must skip keys starting with `_` (T06 stores `_clifpy_version`) — implement that in Task 7's harness up front.
