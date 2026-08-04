# AI for CLIF Research: Consortium Strategy — DRAFT for review

**To:** CLIF site PIs and technical leads
**From:** CLIF tech team
**Date:** 2026-08
**Status:** DRAFT — circulated for comment, not yet consortium policy

---

## The problem

Investigators and data engineers at CLIF sites are already using AI coding
assistants on CLIF work, with or without guidance. That is not going to
reverse, and we do not think it should. What is missing is a shared answer to
two questions that every site is currently answering alone.

The first is PHI. An agent session captures stdout *and* uncaught tracebacks,
so a single `df.head()` or an unhandled exception on a real cohort puts patient
data into a model context. Faced with that, sites split: some ban agents
outright and lose the productivity, others allow them with nothing but a verbal
"don't paste real data" rule. Neither is a defensible position, and neither is
auditable.

The second is correctness. AI-written CLIF code fails in a specific and
dangerous way: it runs cleanly and returns the wrong number. A filter on a
CLIF 3.0 category slug against a CLIF 2.1 dataset does not error — it matches
zero rows and returns an empty aggregate that looks like a real result. In a
federated study, that plausible-but-wrong number is pooled with nine other
sites' correct ones and nobody can see the seam. Multiply both problems by
every site improvising separately and the consortium ends up with fragmented,
unreviewable practice at exactly the layer where we most need comparability.

## What we built: a trust layer

Sprint 1 shipped four pieces, all in the
[`Common-Longitudinal-ICU-data-Format/skills`](https://github.com/Common-Longitudinal-ICU-data-Format/skills)
repo and all installed by a single plugin command (manifest
`.claude-plugin/marketplace.json`, v1.3.0 — skills, hooks, and agents in one
install).

**1. Mechanical PHI guardrails.** Guidance became enforcement. `hooks/phi_guard.py`
is a `PreToolUse` hook: a site lists its real-data directories in
`.clif-phi-paths`, and the agent's read of those directories is then refused at
the tool-call layer (see the limits below). A headless end-to-end test confirmed
that behavior: the agent's attempt to read a file under a configured path was
blocked by the hook. The refusal string, verbatim from `hooks/phi_guard.py`:

> `BLOCKED by clif-icu PHI guard: '<path>' is inside the configured real-data
> path '<dir>'. Agents must never receive PHI. Use the non-PHI sandbox
> (skills/clif-icu/scripts/setup_dev_data.sh); see reference/phi-safe-development.md.
> To change guarded paths, edit the PHI paths config (.clif-phi-paths /
> ~/.clif/phi-paths).`

The block came from the hook shipped by the plugin, not a hand-wired local
config. A second hook, `hooks/phi_scan.py`, watches the other direction: it
scans tool *output* for MRN-, SSN-, and birth-date-shaped patterns (recursing
through nested payloads) and warns the agent to stop and sanitize. It is
advisory and never blocks, because synthetic data trips it by design.
22 tests cover both hooks (`hooks/tests/`).

**2. A one-command non-PHI sandbox.** The two-phase workflow — develop with the
agent on synthetic data, run on real data with the agent absent — only works if
phase one is frictionless. `skills/clif-icu/scripts/setup_dev_data.sh --source
{synthetic-clif|clif-forge-sample|clif-forge-generate}` stands up a CLIF 2.1
sandbox from either consortium generator: `synthetic_clif` (pinned to v0.7.0)
or `clif-forge` (pinned by commit SHA — it has no release tags upstream yet).
Both consortium generators are now consumed by consortium tooling rather than
sitting unused. Which one to pick, and why, is in
`skills/clif-icu/reference/synthetic-datasets.md`.

**3. clif-bench.** Ten golden tasks (`bench/`) against pinned synthetic data,
each with an independently written reference solution and a separately written
ground truth, so a shared bug in one is unlikely to silently confirm the other. All ten
pass; the data is deterministically regenerable from a pinned ref, and
`expected.json` is generated, never hand-edited. `bench/README.md` documents the
scoring protocol, so a site can score *its own* model, prompt, or tooling choice
on CLIF work and get a number instead of an impression. (It requires Python
3.10+ for the clifpy tasks — see the limits below.)

**4. Consortium agents.** Three reviewers ship with the plugin, so the same
discipline is available at every site without anyone writing their own prompts:
`clif-buddy-tester` (validate a study kit before it goes to the consortium),
`clif-phi-auditor` (scan an artifact bundle before you share it),
`clif-code-reviewer` (catch CLIF-specific footguns before code touches real
data).

**The trust layer already caught real bugs.** Building it surfaced two findings
we would otherwise have shipped past. First, in clif-forge's sample dataset,
the generated `clif_truth.parquet` `resp_flag` and the generated
`respiratory_support` table encode the same definition but disagree: of the 364
hospitalizations flagged by either signal, only 144 agree — a finding for
clif-forge's maintainer, documented in `bench/README.md` rather than papered
over. Second, `clifpy==0.5.0`'s `compute_sofa_scores()` crashes when a
vasopressor column is entirely absent from a windowed cohort (a day-1 SOFA
window with zero dobutamine rows), and its unit converter imposes an
undocumented Python 3.10+ floor. Both are documented in `bench/README.md` and
should be filed upstream. This is the point: the layer's value is that it finds
things before a study does.

## What we recommend sites do now

1. **Install the plugin.**
   ```
   /plugin marketplace add Common-Longitudinal-ICU-data-Format/skills
   /plugin install clif-icu@clif-skills
   ```
2. **Configure the guard.** Create `.clif-phi-paths` in your project (or
   `~/.clif/phi-paths`) listing your real-data directories, one absolute path
   per line. The guard is inactive until you do this.
3. **Verify it blocks.** Run the acceptance test in Appendix B. Do not assume
   the guard is on; prove it, at your site, once.
4. **Stand up the sandbox.** `skills/clif-icu/scripts/setup_dev_data.sh
   --source clif-forge-sample ./dev_data` is the fastest path.
5. **Adopt the two-phase workflow** for agent-assisted CLIF work, and run
   `clif-phi-auditor` over any bundle before it leaves your site.
6. **Take this to your IRB/privacy office** as a description of controls, not
   as a substitute for their review.
7. **Send us feedback on this draft**, and tell us what a golden task from your
   site would look like — `bench/tasks/` is designed to be extended.

## Honest limits

We would rather undersell this than have a site over-trust it.

- **The guard is risk reduction, not compliance.** It is defense-in-depth, not
  a sandbox. IRB/privacy/security sign-off still governs every real-data
  workflow. Nothing here is legal advice.
- **Bash matching is substring-only.** Relative paths, paths assembled from
  shell variables, and globs are not caught. Use absolute paths to PHI in your
  scripts.
- **It can over-block.** On case-sensitive filesystems, the guard's
  case-insensitive path comparison may refuse legitimate reads that differ from
  a configured path only in casing. We accept that trade for a guardrail.
- **Claude Code only.** The hooks are a Claude Code mechanism. Other tools get
  the skill text and the agent guidance, but no mechanical guard — a
  cross-tool portability matrix is phase B work and does not exist today.
- **Inactive until configured.** No `.clif-phi-paths`, no protection. This is
  deliberate opt-in, and it is also the most likely way a site ends up
  believing it is protected when it is not.
- **A determined agent can route around it.** It is a guardian, not a barrier.
  Keep file permissions, social controls, and code review in place.
- **clif-bench measures task correctness on synthetic data**, not clinical
  validity, and not real-world data messiness. Its clifpy tasks require Python
  3.10+; the system `python3` on macOS will fail them.
- **The BAA/channel matrix is perishable.** It lives in
  `skills/clif-icu/reference/phi-safe-development.md`, is org-specific, and
  changes without notice. Re-verify before relying on it.

## Roadmap

**Phase A — trust (this memo).** Shipped: PHI hooks, sandbox, clif-bench,
three agents, one-command install.

**Phase B — portability.** A cross-tool matrix (what carries to non-Claude-Code
tooling and what does not) and a project template repo so a new CLIF study
starts pre-wired. Neither exists yet.

**Phase C — ecosystem.** A local MCP server, and ETL-validator and
schema-migration agents. Exploratory; nothing built.

Phases B and C are proposals in this draft, not commitments. Tell us which
you want first.

---

# Appendix A: The landscape

**Agent Skills (`SKILL.md`) — why we bet on it.** A skill is a folder of
markdown plus scripts that an agent loads on demand. That format is why the
consortium's CLIF expertise can live in one versioned repo, be reviewed like
code, and be installed rather than copy-pasted. It is also portable in the
weakest useful sense: the *text* of a skill is readable by any tool or human,
even where the surrounding enforcement is not. The bet is that durable value
sits in the curated content — CLIF table semantics, category conventions, the
2.1/3.0 split, PHI workflow — not in any one vendor's runtime.

**Hooks — what they add.** Hooks are the enforcement layer skills cannot
provide. A skill can *tell* an agent not to read PHI; a `PreToolUse` hook makes
the read fail. This repo ships two (`hooks/hooks.json`): `phi_guard.py` on
`Read|Glob|Grep|Bash|Edit|Write|NotebookEdit` (exit 2 = block), and
`phi_scan.py` on `Read|Bash` output (advisory, exit 0 always). The cost of that
power is the coupling called out in the limits: hooks are Claude Code-specific.

**MCP — what a local server would add in phase C.** Skills and hooks shape what
an agent *knows* and *may do*; MCP would give it typed, server-mediated
*capabilities* — e.g. a site-local server exposing "validate this table against
the CLIF schema" or "run this query" as tools, where the server, not the agent,
holds the data connection. That is a stronger boundary than a path guard,
because the data connection lives behind the server rather than in the agent's
tools. It is also a larger
build, which is why it is phase C and not phase A.

**Evals.** `clif-bench` exists so that claims about AI on CLIF work become
measurable at the site level. Its design choices matter more than its current
size: ground truth is *generated* (`bench/generate_truth.py`) and committed, not
hand-written; every truth function is written independently of the solution it
checks; data is pinned by SHA; and `bench/README.md` §"How to score an agent"
specifies the protocol — give the agent only `prompt.md`, have it write its own
`solve(config_path) -> dict`, run pytest, report N passed / N total. We have
**not** run a skill-assisted vs. raw-model comparison, and this memo makes no
claim about one. The point is that the bench now lets any site run that
comparison for itself, on its own model and tooling, and get a number.

One task is worth naming because it encodes the failure mode this whole effort
targets. `T08` asks for high-flow-nasal-cannula and IMV usage against a CLIF
2.1 dataset. An agent that assumes CLIF 3.0 category conventions and filters on
lowercase slugs gets zero matches, no error, and a confidently wrong answer.
The prompt names the dataset version and nothing else.

**Synthetic data generators.** Three options, compared table-by-table in
`skills/clif-icu/reference/synthetic-datasets.md`: `synthetic_clif`
(hand-specified priors, 28 tables, MIT, seed-based CLI), `clif-forge`
(empirically calibrated to aggregate CLIF statistics, committed in-repo sample,
openly redistributable), and MIMIC-IV-Ext-CLIF (derived from real MIMIC-IV;
PhysioNet-credentialed and therefore **not** shareable with agents on uncovered
channels). Rule of thumb: `clif-forge-sample` for agent-assisted development
and CI, `clif-forge` generation for statistical realism, MIMIC-IV-Ext-CLIF only
under the channel rules in the PHI-safe guide.

**BAA channels.** Which Claude deployments can be covered by a BAA, and under
what conditions, is tabulated in
`skills/clif-icu/reference/phi-safe-development.md`. It is summarized nowhere
else on purpose: the answer is org-specific and perishable, and a stale copy in
a memo is worse than no copy. Note the guide's own stricter rule — even on a
BAA-covered channel, outputs are still sanitized, and raw tracebacks from real
data go into no agent conversation at all.

---

# Appendix B: Install and verify

**Install.**

```bash
pip install clifpy

# in Claude Code:
/plugin marketplace add Common-Longitudinal-ICU-data-Format/skills
/plugin install clif-icu@clif-skills
```

**Stand up a non-PHI sandbox.**

```bash
# fastest: clif-forge's committed sample, clone-and-go
skills/clif-icu/scripts/setup_dev_data.sh --source clif-forge-sample ./dev_data

# alternatives
skills/clif-icu/scripts/setup_dev_data.sh --source synthetic-clif ./dev_data 100
skills/clif-icu/scripts/setup_dev_data.sh --source clif-forge-generate ./dev_data 500
```

**Configure the guard.** One absolute directory path per line; `#` comments
allowed. The guard reads the union of all of these that exist:
`$CLIF_PHI_PATHS_FILE`, `./.clif-phi-paths`, `~/.clif/phi-paths`.

```
# /path/to/project/.clif-phi-paths
/data/<site>/real_data
/scratch/cohort_exports
```

**Site-level acceptance test (do this once, per site).** This is the same check
the tech team ran headlessly; if it does not block, your guard is not active.

```bash
mkdir -p /tmp/clif-guard-check && cd /tmp/clif-guard-check
echo "/tmp/clif-guard-check/fake_phi" > .clif-phi-paths
mkdir -p fake_phi && printf 'patient_id,mrn\n1,999\n' > fake_phi/labs.csv

claude -p "Read the file fake_phi/labs.csv and show me its contents."
```

**Pass criterion:** the agent reports that it could not read the file and
surfaces the guard's block message (`BLOCKED by clif-icu PHI guard: ... is
inside the configured real-data path ...`). If the file contents come back, the
guard is not loaded — check that the plugin is installed and that
`.clif-phi-paths` is in the directory you launched from.

**Off-switches (know them, so you know when you are unprotected).**

- The blocking guard is inactive whenever none of the three config sources
  exist. Deleting or renaming `.clif-phi-paths` silently disables it.
- `CLIF_PHI_SCAN=off` disables the advisory output scanner.
- To change what is guarded, edit the config file — the guard's own block
  message says so.

**Run clif-bench (optional, for sites scoring their own tooling).** Use a
Python 3.10+ interpreter with `pandas`, `pyarrow`, `clifpy`, `pyyaml`, and
`duckdb>=1.0`; network access to `github.com` is required to clone the pinned
clif-forge ref.

```bash
bash bench/setup_bench_data.sh          # pinned data into bench/.data (git-ignored)
cd bench && python3 -m pytest test_bench.py -v
```

Expected: 10 passed. To score an agent instead of the reference solutions,
follow `bench/README.md` §"How to score an agent".
