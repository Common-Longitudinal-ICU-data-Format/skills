---
title: Harden, verify, and generalize PHI-safe agentic development for all CLIF coding
date: 2026-07-22
type: feature
origin: Follow-up to 2026-07-22-003 — user directive to make the PHI-safe workflow prescriptive, verify time-sensitive claims via ref/tavily, and govern ALL CLIF agentic coding
status: implemented — edits applied & verified 2026-07-22; shipped as a SINGLE PR off main (branch phi-safe-agentic-development, marketplace 1.1.0→1.2.0), distinct from PR #2 — see "Delivery update" below
artifact_readiness: implementation-ready
artifact_kind: ce-unified-plan/v1
product_contract_source: ce-plan-bootstrap
---

# Harden, verify, and generalize PHI-safe agentic development for all CLIF coding

## Goal Capsule

The `003` work shipped a PHI-safe section (`SKILL.md`) + reference guide
(`reference/phi-safe-development.md`) + bootstrapper (`scripts/setup_dev_data.sh`).
This plan **hardens** that content against three defects surfaced by MCP
verification, **generalizes** it from "clif-icu analysis flows" to **any agent
writing or debugging CLIF code**, and makes the canonical workflow **prescriptive
and numbered** so users actually follow it:

1. **Develop against non-PHI data** — the agent never sees PHI/RHI. Claude
   Enterprise is recommended *if the org has it*, but any channel (Max/Pro or the
   first-party API) is fine for this step because the agent only sees synthetic data.
2. **The user runs the code on real PHI/RHI themselves**, manually, in their own
   secure environment — the agent is absent.
3. **To debug real-data errors, sanitize first; if you have a HIPAA-compliant chat,
   move the debugging there** — otherwise sanitize and stay non-PHI.

Three verified corrections must land as blocking fixes: (a) the BAA/covered-channel
framing is now inaccurate (the HIPAA-ready Claude **API** no longer requires ZDR,
and ZDR + HIPAA-readiness live on **separate orgs** — so the current "Claude Code
covered only with ZDR" table row conflates two distinct products); (b) the
`synthetic_clif` generation command in the bootstrapper is guessed, not the verified
CLI; (c) the two example scripts read config keys (`tables_path`/`file_type`) that
`create_example_config` never writes, so the demo config silently fails with them.

Non-goals: rewriting clifpy internals, CLIF v3.0 content, the 2.1.1-currency claim
(flagged, deferred to PR #2), the git branch/PR (separately-confirmed final step),
and the parked OA-equity work.

## Product Contract

### Problem & audience

CLIF researchers are already using AI agents to write and debug ICU-data code. The
governing safety requirement is absolute: **PHI/RHI must never reach the agent.**
The shipped guidance is correct in spirit but (1) reads as advice specific to
clif-icu *analysis*, not a rule binding *all* CLIF code authoring; (2) contains
time-sensitive BAA claims that verification has shown to be inaccurate; and (3)
ships a bootstrapper and example scripts that will not actually run as written.

### Requirements (traceable to the user directive)

- **R1 — Prescriptive numbered workflow.** State the canonical 3-step workflow
  (non-PHI dev — Enterprise recommended, but any channel incl. Max/Pro or API fine
  since the agent never sees PHI → manual PHI execution by the user → sanitized,
  optionally HIPAA-chat debugging) as clearly-numbered rules users can follow
  verbatim. Address head-on that people *are* using agents to write CLIF code.
- **R2 — Generalize scope.** The rule is a **universal principle for any agent
  writing/debugging CLIF code** (clifpy, R packages, ETL, ad-hoc scripts) — not
  only clif-icu analysis. Framing must say so explicitly, while being honest about
  the **enforcement boundary**: this skill *states and self-enforces* the rule
  within clif-icu work, and the principle *applies everywhere* you use an agent with
  CLIF data. Do not overclaim that one skill enforces behavior outside its own load.
- **R3 — Correct the BAA/covered-channel facts** (blocking accuracy fix). Reflect
  the verified distinctions (API vs Claude Code, separate orgs, Covered Models,
  expanded exclusions). Keep the "not legal advice / verify / re-check" posture.
- **R4 — Harden the bootstrapper** to the verified `synthetic_clif` CLI and a
  `python3` fallback, canonical repo URL.
- **R5 — Fix the config-key mismatch** so the demo config actually loads in the two
  example scripts (accept both `data_directory`/`filetype` and `tables_path`/`file_type`).
- **R6 — Reconcile the "MIMIC demo dataset in clifpy" claim accurately.** clifpy
  ships **no** bundled demo loader (verified against the clifpy README + docs this
  session). Present the real options honestly.
- **R7 — Decouple the version note** from a hard 2.1.1 assertion; flag the
  unverified 2.1.1 claim for PR #2 rather than repeating it.

### Explicit non-goals

Same as Goal Capsule. No new CLIF v3.0 content; no clifpy internals; no PR/branch
in this pass; do not "fix" the 2.1.1 claim here (flag only).

## Planning Contract

### Verified facts (ref + tavily, 2026-07-22)

| Claim | Verification result | Consequence for plan |
|-------|---------------------|----------------------|
| HIPAA-ready Claude **API** requires ZDR | **False now** — HIPAA-readiness no longer requires ZDR; they are configured on **separate orgs** (distinct org IDs) and cannot coexist | Rewrite §4 table; split API from Claude Code |
| Claude **Code** BAA coverage | Covered **only with ZDR**, on a qualified first-party API org **or Claude Enterprise** | Keep ZDR requirement scoped to Claude Code, not API |
| Bedrock / Vertex | Covered under **AWS** BAA / **Google Cloud** BAA respectively (cloud provider is the business associate; Anthropic BAA does not apply) | Keep, attribute BAA to the correct provider |
| Covered Models (e.g. Fable 5, Mythos 5) | **Cannot** be BAA-covered in Claude Code / Cowork | Add as a gotcha |
| Exclusions | Free/Pro/Max/Team, Console/Workbench, **Cowork**, beta features, **web search** | Expand "never covered" list |
| Structured outputs + PHI | Do **not** place PHI in JSON schema `names`/`enum`/`const`/`pattern` | Add one-line note to sanitization section |
| `synthetic_clif` CLI | `python -m synthetic_clif --patients N --hospitalizations N --output PATH --seed 42 --format parquet\|csv [--workers N] [--no-concept-tables]` (defaults 10/12/`data`/42/parquet); verified via docs/tavily 2026-07-22, **not** executed against the installed package | Bootstrapper uses this invocation **and** tells users to run `python -m synthetic_clif --help` as ground truth if it fails |
| `synthetic_clif` repo URL | Both `Common-Longitudinal-ICU-data-Format/synthetic_clif` and `AartikSarma/synthetic_clif` resolve to the **same HEAD commit** (`git ls-remote`, 2026-07-22) — same fork network, either clones | Use the CLIF-org URL as canonical (matches skill owner); the swap is a consistency fix, **not** clone-breaking — de-escalated from "blocking" |
| clifpy bundled demo / MIMIC demo loader | **None found** in the clifpy README + published docs (checked 2026-07-22, v0.5.0) — absence-of-documentation, not proven absence-in-package | Reconcile R6 as an observation ("no documented demo loader found; confirm against your installed version"), not a flat existential negative |
| Open non-credentialed MIMIC option | "MIMIC-IV Clinical Database Demo" — 100 patients, de-identified, **excludes free-text notes**, ODbL license, PhysioNet/Kaggle/AWS — but **raw MIMIC-IV, not CLIF-formatted, not in clifpy** | Mention as a real non-PHI option with accurate caveats |
| MIMIC-IV-Ext-CLIF | CLIF-formatted, **credentialed + DUA-gated**, 14 tables | Keep as co-equal, agent-must-not-fetch |
| CLIF 2.1.1 published tag | **Not found** via ref/tavily; official data dictionary = 2.1.0 | Decouple version note; flag for PR #2 |

### Approach & rationale

Edit the three shipped files in place plus the two example scripts; no new files.
The reference doc is the deep surface (absorbs the corrections + reconciliation);
`SKILL.md` carries the tightened, generalized, prescriptive summary; the two scripts
get a minimal, additive config-loader shim. Corrections are blocking; the 2.1.1
claim is flagged, not resolved (owned by PR #2). Version bump already at 1.3.0 — no
further bump needed for a same-minor hardening pass unless the user wants 1.3.1.

### Delivery update (supersedes the two-PR plan below)

The two-PR split proved impractical: the PHI-safe work (003+004) had been authored
on top of the unmerged PR #2 branch, and PR-A/PR-B edits were interleaved in the
same hunks of shared files (SKILL.md, marketplace.json, cohort script, configuration.md)
with `git add -p/-i` unavailable. **Per user decision, the work ships as a SINGLE PR
off `main`** (branch `phi-safe-agentic-development`), combining 003+004 and kept
distinct from PR #2. The shared files were reconstructed on `main`'s baseline so the
diff contains **only** PHI-safe changes — no PR #2 content (no 2.1.1 version block,
`clif_version` config row, `check_clifpy_currency` section, or the cohort `load_table`
kwarg fix, all of which remain owned by PR #2). Because this branch is off `main`
(1.1.0), the marketplace bump is **1.1.0 → 1.2.0** (not 1.3.0, which assumed sitting
on PR #2's 1.2.3); the version will reconcile with PR #2 at merge time.

The original two-PR plan is retained below for historical context.

### Delivery: two PRs (correctness fast-track, bets separate)

Per user decision, the work ships as **two PRs**, both distinct from the unmerged
v2.1.1-currency PR #2. The split cuts **through** U1 and U6 (each holds both
correctness content and product bets), so it is applied at the **sub-item** level,
not whole-unit:

| PR | Content | Units / sub-items |
|----|---------|-------------------|
| **PR-A — correctness (fast-track)** | Unambiguous fixes to make shipped artifacts accurate/working; independently landable | U1 §4 BAA-facts rewrite (R3); U1 §1 URL fixes (F3) + Known-wrinkle rewrite (F4); U1/U6 unconditional "never paste raw PHI" guard + A1 relaxing-facts gate; **U2** (structured-output sanitization note); **U3** (version-note decoupling + 2.1.1 flag); **U4** (synthetic_clif CLI + `$PY`); **U5** (config-key `KeyError` + PHI-leak hardening: demo-config default, shape/columns not paths/rows); **U7** (SOFA script: demo-config default, summary not `head(10)`) |
| **PR-B — product bets (discussion)** | Judgment calls that may draw review debate; must not hold PR-A hostage | U1 intro + U6 lead: R1 prescriptive numbered workflow & Enterprise-recommended framing; R2 all-CLIF-coding scope generalization (incl. the retitle) |

**Sequencing:** land PR-A first (or in parallel); PR-B rebases on top. Because both
touch `phi-safe-development.md` intro and `SKILL.md` §PHI-safe, whichever lands
second rebases the shared hunks — keep PR-B's diff limited to the framing/scope
prose so the rebase is mechanical. If PR-B stalls in review, PR-A still delivers all
correctness value on its own.

### Pattern references

- `reference/phi-safe-development.md` §4 table + Q1–Q4 gate — the edit target for R3.
- `create_example_config` canonical keys (`reference/clifpy_utils/configuration.md`).
- Existing YAML-variant mapping note (`configuration.md` §"YAML Alternative").

## Implementation Units

### U1 — Rewrite `reference/phi-safe-development.md` intro + §4 (R1, R2, R3, R6)

**Files:** `skills/clif-icu/reference/phi-safe-development.md`

- **Intro/threat model:** broaden the opening so it explicitly states the rule as a
  **universal principle for any agent writing/debugging CLIF code** (clifpy, R
  packages, ETL, ad-hoc scripts) — not just clif-icu analysis — with one honest
  sentence on the enforcement boundary (this skill self-enforces within clif-icu
  work; the principle applies everywhere you use an agent with CLIF data). Add a
  short "People are already using agents to write CLIF code — here is how to do it
  safely" framing, then the numbered canonical workflow (R1):
  1. Develop against **non-PHI/demo data**. If your org has **Claude Enterprise**,
     use it here too (one less channel to switch). But **any** channel — a consumer
     **Max/Pro** plan or the **first-party API** — is fine for this step, *because
     the agent only ever sees synthetic data.* A BAA-covered channel becomes
     **required only at step 2 / Phase B**, when real PHI is involved. (Resolves the
     SKILL.md line-26 "Max/Pro is fine here" statement — it is accurate for dev.)
  2. **You run the code on real PHI/RHI yourself**, manually, in your secure env.
  3. To debug real-data errors, **sanitize first; if you have a HIPAA-compliant
     chat, move debugging there** — otherwise sanitize and stay non-PHI.
- **§1 dataset table (R6):** keep `synthetic_clif` as the primary no-paperwork
  option. Correct any implication that clifpy bundles a demo — but state it as an
  **observation**, not a flat existential negative: *"No documented bundled demo
  loader was found in the clifpy README/published docs (checked 2026-07-22,
  v0.5.0); confirm against your installed version."* (The user reported the
  opposite, so hedge to what was actually verified — see the verified-facts row.)
  Add a third row: the open **MIMIC-IV Clinical Database Demo** (100 patients, no
  free-text notes, ODbL — note the attribution/share-alike license obligation) as a
  real non-PHI option, with the accurate caveat that it is **raw MIMIC-IV, not
  CLIF-formatted** (needs the CLIF-MIMIC ETL) — distinct from the credentialed,
  CLIF-formatted MIMIC-IV-Ext-CLIF. Keep the "agent must not fetch credentialed
  MIMIC" rule crisply separate from this open-demo row so a reader does not
  over-generalize "the agent can fetch MIMIC" toward the credentialed dataset.
- **§1 URL + known-wrinkle cleanup (F3, F4):** replace **both** `AartikSarma`
  `synthetic_clif` URLs in this doc (the §1 link and the `git clone …` in the
  quick-setup block) with the canonical CLIF-org URL, so the reference doc,
  `SKILL.md` (U6), and the bootstrapper (U4) all agree. **Update or remove** the §1
  "Known wrinkle" note that currently says the example scripts read
  `tables_path`/`file_type` and that reconciling them is "future work" — after U5
  that note is stale (and it wrongly implicates the SOFA script, which reads no
  config keys). Rewrite it to reflect the post-U5 state.
- **§4 rewrite (R3, blocking):** replace the covered-channel table with:
  - Row: **First-party Claude API (HIPAA-ready org)** — Anthropic BAA — *does not
    require ZDR*; HIPAA-readiness and ZDR are configured on **separate orgs**.
  - Row: **Claude Code** — Anthropic BAA — covered **only with ZDR**, on a
    qualified first-party API org **or Claude Enterprise**.
  - Row: **Claude Enterprise** — Anthropic BAA.
  - Row: **Bedrock / Vertex** — **AWS / Google Cloud** BAA (cloud provider is the
    business associate).
  - **Gotcha:** Covered Models (e.g. Fable 5, Mythos 5) **cannot** be BAA-covered
    in Claude Code / Cowork.
  - **Never covered:** Free/Pro/Max/Team, Console/Workbench, **Cowork**, beta
    features, **web search**.
  - Update the Q1–Q4 gate so Q3 (ZDR) is scoped to **Claude Code**, not the API.
- **Relaxing-facts gate (A1, safety-critical framing):** this rewrite *loosens* a
  prior constraint (API no longer needs ZDR). A reader who over-trusts a stale
  snapshot could send PHI on a channel that is not actually covered *for their org*.
  So the §4 rewrite must carry a **conspicuous** (bold, adjacent to the table, not
  buried in the footer) instruction to **confirm the current BAA/ZDR/covered-model
  status for your own org before any PHI flows** — these facts are perishable and
  org-specific. The relaxation is documented, never presented as a standing
  guarantee.
- **Preserve the unconditional "never paste raw PHI" guard (A3, safety-critical).**
  A BAA-covered channel is **not** a license to paste raw PHI, tracebacks, IDs,
  dates, note text, or dataframe previews into an agent conversation. The §4 rewrite
  and the step-3 "HIPAA-compliant chat" language must not weaken this: even on a
  covered channel, the default remains sanitize-first, and the "never paste raw
  PHI/RHI or raw tracebacks into ANY agent conversation" rule (from §3 and the
  intro) stays unconditional. State explicitly that "move debugging to a
  HIPAA-compliant chat" reduces channel risk but does **not** relax the
  sanitization/minimization rule.
- Keep timestamp ("as of 2026-07, verify before relying"), official links, and the
  bold "not legal/compliance advice" disclaimer.

**Test scenarios (doc-level verification):**
- The word "Enterprise" appears in the numbered workflow step 1.
- §4 has distinct rows for API vs Claude Code; the API row does **not** assert ZDR.
- "separate org", "Covered Models", "Cowork", and "web search" all appear.
- No sentence states clifpy bundles/ships a demo dataset.
- A conspicuous (bold, table-adjacent) "confirm current BAA/ZDR/covered status for
  your org before any PHI" instruction is present (A1).
- The unconditional "never paste raw PHI/RHI or raw tracebacks into ANY agent
  conversation, even a covered one" guard survives in both the intro and §4 (A3);
  no AartikSarma `synthetic_clif` URL remains in the doc (F3); the stale "Known
  wrinkle" note is rewritten to the post-U5 state (F4).

### U2 — Sanitization hardening: structured-output note

**Traceability:** this unit does **not** derive from R3 (R3 is scoped to the
BAA/covered-channel facts). It hardens the existing §3 **sanitization** guidance
and traces to the Planning-Contract verified-fact row *"Structured outputs + PHI —
do not place PHI in JSON schema `names`/`enum`/`const`/`pattern`."* Treat it as an
additive sanitization rule, co-equal with the existing "never paste raw
IDs/dates/tracebacks" bullets.

**Files:** `skills/clif-icu/reference/phi-safe-development.md` §3

- Add one bullet: when using **structured outputs / JSON schema**, never place PHI
  in schema `names`, `enum`, `const`, or `pattern` values — these are transmitted
  verbatim and are not "data" the model merely reads.

**Test scenario:** §3 mentions JSON-schema `enum`/`const`/`pattern`.

### U3 — Version-note decoupling + 2.1.1 flag (R7)

**Files:** `skills/clif-icu/reference/phi-safe-development.md` §6

- Reword §6 so it does **not** independently assert a published CLIF 2.1.1. State
  that `synthetic_clif` emits **CLIF 2.1.0** (the current official data dictionary
  version), that this is dev-safe for code authoring, and **defer** any 2.1.0-vs-
  2.1.1 delta discussion to `SKILL.md`'s version block (single source of truth).
- Add a one-line planner-facing flag (HTML comment or "Note:") that the skill-wide
  2.1.1 claim is **unverified against a published tag** and is owned by PR #2 — do
  not resolve here.

**Test scenario:** §6 no longer contains a standalone factual claim that 2.1.1 is
published; it points to `SKILL.md`.

### U4 — Harden `scripts/setup_dev_data.sh` (R4)

**Files:** `skills/clif-icu/scripts/setup_dev_data.sh`

- Line ~33: `command -v python` → prefer `python3`, fall back to `python`
  (resolve into a `$PY` var; the repo's environment has no `python` on PATH).
- Line ~27: `REPO_URL` → canonical
  `https://github.com/Common-Longitudinal-ICU-data-Format/synthetic_clif`.
- **Route ALL python/pip invocations through `$PY` (verified — the script uses
  more than the two lines the first pass named):** the bare `pip install -e .`
  (line ~51) and the bare `python - <<'PY' … PY` config heredoc (line ~87) both
  still assume a `python`/`pip` on PATH and will abort the whole script under its
  `set -euo pipefail`. Change the install to `"$PY" -m pip install -e .` and the
  heredoc launcher to `"$PY" - <<'PY'`. Grep the finished script to confirm **no**
  bare `python`/`pip` invocation remains.
- Lines ~59–72: replace the guessed generation block with the **verified** CLI:
  `"$PY" -m synthetic_clif --hospitalizations "$N_HOSP" --output "$DEST_DIR" --format parquet --seed 42`
  (drop the `generate` subcommand and `--n` guesses). Keep the small default N for
  fast agent-loop iteration.
- Keep the `create_example_config` heredoc (canonical keys) and PHI-safe reminders.

**Test scenarios:**
- `bash -n skills/clif-icu/scripts/setup_dev_data.sh` passes (syntax only; do not
  execute the clone/install/generate in this pass).
- Grep confirms the canonical org URL and no remaining `python -m synthetic_clif
  generate` / `--n` tokens.
- Grep confirms **no** bare `python ` or `pip ` invocation remains — every call is
  `"$PY" …` (guards the `set -euo pipefail` abort at lines ~51 and ~87).
- `$PY` resolution prefers `python3`.

### U5 — Fix config-key mismatch in `cohort_identification_example.py` (R5)

**Files:** `skills/clif-icu/scripts/cohort_identification_example.py`

- **Scope correction (verified by reading both scripts):** only
  `cohort_identification_example.py` reads raw config-dict keys
  (`config['tables_path']` / `config['file_type']`, lines ~32–41) and therefore
  `KeyError`s on a `create_example_config`-written JSON. `sofa_score_calculation.py`
  uses `ClifOrchestrator(config_path=CONFIG_PATH)` and **reads no config-dict keys**
  — clifpy parses the config natively — so it needs **no loader shim**. Do not touch
  its config loading. (If desired, U6/U4 can align its default `CONFIG_PATH` to the
  demo config the bootstrapper writes, but that is a one-line default, not a shim.)
- In `cohort_identification_example.py`, add a tiny loader shim that accepts
  **both** key sets: read `data_directory` else `tables_path`; `filetype` else
  `file_type`. Minimal, additive; preserve existing behavior when the YAML-variant
  keys are present.
- **PHI-leak hardening (S1, safety):**
  - **Default `CONFIG_PATH` to the non-PHI demo config** the bootstrapper writes
    (`./clif_demo_config.json`) instead of `../config/config.json` — a naive run
    then hits synthetic data, not the researcher's likely-real config. Keep the path
    overridable (env var / arg) for real runs the researcher does themselves.
  - **Do not print PHI-derived values.** Replace `print(config['tables_path'])`
    (real path) and any real-row preview with **shape + column names only**
    (`df.shape`, `list(df.columns)`), so a watching agent never sees real paths or
    row values. This also removes the `KeyError` on the old key.
- Keep the PHI-SAFE banner comment.

**Test scenarios:**
- A JSON config written by `create_example_config` (keys `data_directory`/
  `filetype`) loads without `KeyError` in `cohort_identification_example.py`
  (static read-through of the loader block; no real data run required).
- A YAML-variant config (`tables_path`/`file_type`) still loads (back-compat).
- The default `CONFIG_PATH` points at the non-PHI demo config, not
  `../config/config.json`.
- No `print` statement emits a config path or raw dataframe rows — only shapes /
  column names.

### U6 — Tighten `SKILL.md` PHI-safe section (R1, R2, R3)

**Files:** `skills/clif-icu/SKILL.md` (lines ~22–36)

- Generalize the lead sentence to "any AI agent that helps write or debug **CLIF
  code**" (R2).
- Reframe the numbered list to the prescriptive canonical workflow (R1): step 1
  recommends **Claude Enterprise** *if the org has it* but states plainly that any
  channel — Max/Pro **or** the first-party API — is fine for non-PHI dev (the agent
  never sees PHI); covered channel required only at step 2/Phase B. Keep the shipped
  line-26 "Max/Pro is fine here" note — do not delete it; it is accurate for dev.
  Step 2 = user runs on PHI manually; step 3 = sanitize + optional HIPAA-compliant
  chat for debugging.
- Correct step 3's covered-channel parenthetical to match U1 (API needs no ZDR;
  Claude Code needs ZDR; separate orgs) without bloating the always-loaded surface —
  one tightened sentence, defer detail to the reference doc.
- **Preserve the unconditional "never paste PHI" guard (A3).** The existing
  line-33 "Never paste PHI" rule stays, and step 3 must not imply that a
  HIPAA-compliant chat lets you paste raw PHI/tracebacks — covered channel reduces
  channel risk, sanitize-first still applies. Do not soften this in the tightening
  pass.
- Fix the `synthetic_clif` link to the canonical org URL.

**Test scenarios:**
- SKILL.md step 1 names Claude Enterprise.
- SKILL.md no longer implies the HIPAA-ready API requires ZDR.
- The `synthetic_clif` link is the canonical org URL.
- The "Never paste PHI" guard is intact and step 3 does not present the
  HIPAA-compliant chat as a license to paste raw PHI (A3).

### U7 — Stop `sofa_score_calculation.py` from printing PHI-derived rows (S1)

**Files:** `skills/clif-icu/scripts/sofa_score_calculation.py`

- The script uses `ClifOrchestrator(config_path=CONFIG_PATH)` (no dict-key reads —
  needs no loader shim, per U5), but it **prints `sofa_scores.head(10)`**, which on
  real data is PHI-derived rows a watching agent would see.
- **Default `CONFIG_PATH` to the non-PHI demo config** (`./clif_demo_config.json`),
  overridable for the researcher's own real run.
- Replace `print(sofa_scores.head(10))` with a **non-PHI summary** — `df.shape`,
  column names, and/or aggregate score distribution (e.g. `.describe()` on the score
  column only, with small-cell suppression) — never raw per-patient rows.
- Keep the PHI-SAFE banner comment.

**Test scenarios:**
- No `print` emits `head(10)` / raw per-row output; only shape / columns / suppressed
  aggregates.
- Default `CONFIG_PATH` points at the non-PHI demo config.
- The script still runs against the demo config produced by `setup_dev_data.sh`
  (static read-through; no real-data run in this pass).

## Verification Contract

1. `bash -n skills/clif-icu/scripts/setup_dev_data.sh` — syntax clean.
2. `grep -n "Common-Longitudinal-ICU-data-Format/synthetic_clif" skills/clif-icu/scripts/setup_dev_data.sh` — canonical URL present; and no `generate`/`--n` guesses remain.
3. Static read-through of both example-script loaders confirming both key sets load.
4. Markdown link check: every link in the edited reference doc + SKILL.md resolves
   to an existing path; official BAA URLs and dataset URLs are well-formed.
5. Re-read §4 in place to confirm the API row does not assert ZDR and the separate-
   orgs / Covered-Models / Cowork / web-search facts are present.
6. `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"`
   — still valid; version remains `1.3.0` (no bump unless user requests 1.3.1).
7. Confirm no sentence anywhere asserts clifpy bundles a demo dataset (R6).
8. Grep both example scripts: default `CONFIG_PATH` is the non-PHI demo config, not
   `../config/config.json`; no `print` emits a config path, `head(10)`, or raw
   per-row dataframe output (U5, U7).

## Definition of Done

- U1–U7 applied; all Verification Contract checks pass.
- The three blocking corrections (BAA facts, synthetic_clif CLI, config-key
  mismatch) are landed and verified.
- Neither example script defaults to a real-data config or prints PHI-derived
  paths/rows (U5, U7).
- The canonical workflow reads as clearly-numbered prescriptive rules in both
  `SKILL.md` and the reference doc, generalized to all CLIF agentic coding.
- The 2.1.1 claim is flagged for PR #2, not modified.
- **Two-PR split (per Delivery section) is honored:** PR-A (correctness) is
  independently landable and self-contained; PR-B (R1/R2 framing + scope bets)
  rebases on PR-A and can stall without blocking PR-A's value.
- Branch/PRs remain **not started** — deferred to explicit user go-ahead as the
  separately-confirmed final step.
