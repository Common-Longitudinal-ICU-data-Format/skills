# PHI/PII-safe CLIF development

Use this workflow for any coding agent, model, OS, or R/Python stack. Skill
instructions and hooks do not make a data environment compliant.

## 1. Develop with synthetic inputs

Keep real patient files outside the agent's accessible workspace. Use small,
fully synthetic fixtures that exercise the declared CLIF schema, category
values, units, joins, missingness, and failure paths. Public mCIDE files describe
vocabulary; they are not permission to read clinical tables.

Use the project's R or Python environment. Optional larger synthetic sources
are compared in [synthetic datasets](synthetic-datasets.md). Verify the source's
license and provenance; credentialed or real-derived data is not automatically
safe for agent access. Do not download credentialed datasets for an agent.

The [sandbox helper](../scripts/setup_dev_data.sh) requires Bash and its
documented Python dependencies. It is optional, especially for R-only or native
Windows work: a hand-written synthetic fixture is sufficient. Do not claim
that a Bash helper runs in PowerShell or that WSL proves native Windows support.

## 2. Validate before the real-data handoff

Ask for the user's CLIF version and retrieve [matching current mCIDE](current-mcide.md).
Do not infer a version from casing. The examples' `CLIF_SCHEMA_VERSION` setting
is a declaration, not detection or migration; check each example's actual
supported versions and installed APIs before reuse.

Test with synthetic positive, negative, null, malformed, and unknown inputs.
Verify the expected aggregate or score and visible handling of unmapped values.
Preserve source values when normalizing categories. Record dependency versions,
vocabulary commit SHA, commands, and which OS/harness paths were actually tested.

## 3. Researcher-only execution on real data

The researcher runs the validated code separately in their approved environment
with the coding agent absent. No real patient files, previews, raw exceptions,
or unsuppressed outputs enter the agent session. Do not move real data into a
synced coding folder or enable the examples' `CLIF_ALLOW_REAL_DATA` override
while an agent can observe execution.

A provider account, BAA, local model, or enterprise plan does not override this
skill's synthetic-only coding workflow. Deployment eligibility and institutional
approvals belong to the site's privacy/security process.

## 4. Bring back a synthetic reproduction

Reproduce an error using artificial inputs. Share the exception type, relevant
code, and a synthetic fixture. Replace identifiers, dates, paths containing
personal information, and free text with invented placeholders. Review code,
configuration, notebook outputs, and filenames for embedded sensitive content.

Never send real PHI/PII through chat, MCP, web search, telemetry, tool output,
schemas/enums, images, or model-visible logs. An agent running locally may still
capture stdout and errors. Released aggregates need the site's suppression and
privacy review; aggregate output alone does not guarantee anonymity.

## Optional Claude hooks

The plugin's [hook documentation](https://github.com/Common-Longitudinal-ICU-data-Format/skills/blob/main/hooks/README.md)
describes its configured-path guard and advisory output scanner. They are
Claude-specific, inactive or limited under documented conditions, and do not
transfer automatically to Codex, OpenCode, Pi, or another harness. Verify active
protections, keep least-privilege tool access, and retain the same synthetic-only
boundary when hooks are absent.
