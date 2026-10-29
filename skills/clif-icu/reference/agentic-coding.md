# Portable, privacy-safe agentic coding

Use the user's R or Python stack. Read the repository's entry points, dependency
pins, tests, and declared CLIF version before editing. Write the smallest change,
then test it with synthetic fixtures and report what was actually run.

## Harness and model differences

The core `SKILL.md` and its references are instructions, not a permission system.
Use the active harness's available file, search, edit, execution, and MCP tools;
do not assume a model name, tool name, shell, network connection, or context size.

| Harness | Check before acting |
|---------|---------------------|
| Codex | Skill discovery, sandbox/network boundaries, and required command approvals. |
| Claude Code | Plugin agents/hooks are Claude-specific; verify that they are installed, configured, and active. |
| OpenCode | Skill-tool and agent permissions, including access to external directories and network tools. |
| Pi | Skill loading, enabled tools/extensions, and the configured provider; do not assume a sandbox or approval layer. |

Read only the references needed for the task. If automatic discovery fails, load
this `SKILL.md` explicitly through the harness. A missing MCP tool is a reason
to use an approved read-only alternative or report a gap, never to bypass access
controls. Do not install extensions, change providers, or relax permissions as a
side effect of using this skill.

## R and Python

- Use Python/clifpy APIs only after checking the installed version/signatures.
  For R, use the project's R packages and verify their interfaces; do not turn
  Python method names into invented R functions.
- Test column types, join keys/cardinality, units, null handling, categorical
  matching, and expected aggregates. Use synthetic positive and negative cases.
- For nonconforming tables, repair only unambiguous schema-backed names/values.
  Preserve source data and report unmapped or conflicting inputs. Stop affected
  calculations when a safe mapping is unavailable instead of returning plausible zeros.
- Adapt paths, subprocesses, parallelism, encodings, and dependency setup to the
  actual OS using the [compatibility guide](compatibility-review.md).
- Separate code generation, static review, and executed validation. An unavailable
  interpreter or dependency is an untested path, not a passing check.

## Sensitive data

Keep PHI/PII, real patient rows, identifiers, dates, notes, images, raw tracebacks,
and secrets out of model context, tools that return output to the agent, MCP,
web searches, telemetry, and external services. Local execution is not inherently
private: a coding harness can capture stdout and errors. Use synthetic inputs
and allowlisted, privacy-reviewed aggregate outputs with appropriate suppression.

The researcher runs real-data analyses in their approved environment with the
agent absent. Follow [PHI-safe development](phi-safe-development.md). Hooks are
defense in depth, not a sandbox, a BAA, or proof of compliance. These boundaries
apply in every harness and OS, even when its hooks or permission tools differ.

Sources: [Agent Skills](https://agentskills.io/specification),
[Claude authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices),
[Codex skills](https://developers.openai.com/codex/skills),
[OpenCode skills](https://opencode.ai/docs/skills/),
[Pi skills](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md).
