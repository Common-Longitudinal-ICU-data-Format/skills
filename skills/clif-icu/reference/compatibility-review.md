# CLIF code compatibility review

Use this guide when writing or reviewing CLIF Python/clifpy, R, SQL, notebooks,
setup scripts, hooks, or study kits. Review both operating-system portability
and CLIF 2.1/3.0 compatibility. Keep execution within the skill's non-PHI rules.

## Establish the targets

Read the project configuration, dependency pins, entry commands, and declared
CLIF data version. `CLIF_SCHEMA_VERSION` is a declaration, not schema detection,
data migration, or proof that the code supports that version. Check which schema
version loaders, validators, filters, and scoring utilities actually use.

Use the declared version when known. If it is missing, ask the researcher and
continue static review with conditional findings. Do not silently choose a
version or convert data to make the code run. For code claiming both versions,
check each version separately. A project intentionally supporting only one
version should say so and reject unsupported inputs clearly.

## CLIF 2.1/3.0 capitalization and vocabulary

Compare table/column names and categorical literals with the exact version's
data dictionary, mCIDE vocabulary, and installed library schema. Record the
source version/ref and library version. Bundled, unversioned `schemas/` and
`mCIDE/` files do not establish 3.0 support. If a required source is missing or
the library and dictionary disagree, report the mismatch and verification gap.

These respiratory `device_category` examples were checked against the pinned
sources below. Recheck the project's target versions before relying on them:

| CLIF 2.1 | CLIF 3.0 | Review implication |
|----------|----------|--------------------|
| `IMV` | `imv` | A case-sensitive comparison must use the target value. |
| `NIPPV` | `nippv` | Check membership lists as well as equality filters. |
| `High Flow NC` | `hfnc` | Lowercasing or replacing spaces is insufficient. |
| `Room Air` | `room_air` | Spaces and underscores matter along with case. |
| `Expired` | `expired` | A raw case-sensitive comparison can lose deaths. |

Pinned references:

- [CLIF v2.1.1 respiratory device vocabulary](https://github.com/Common-Longitudinal-ICU-data-Format/CLIF/blob/v2.1.1/mCIDE/respiratory_support/clif_respiratory_support_device_categories.csv)
- [clifpy v0.5.0 CLIF 3.0 respiratory schema](https://github.com/Common-Longitudinal-ICU-data-Format/clifpy/blob/v0.5.0/clifpy/schemas/3.0/respiratory_support_schema.yaml)
- [Bundled CLIF 2.1 hospitalization schema](../schemas/hospitalization_schema.yaml) and [clifpy v0.5.0 CLIF 3.0 hospitalization schema](https://github.com/Common-Longitudinal-ICU-data-Format/clifpy/blob/v0.5.0/clifpy/schemas/3.0/hospitalization_schema.yaml)
- [CLIF 3.0 data dictionary](https://clif-icu.com/data-dictionary/data-dictionary-3.0.0)

Inspect equality/`isin`/`IN` filters, joins and mapping keys, `case_when`/`CASE`
recodes, regexes and collation, pivots, category/group/type lists, and clinical
score constants. Check tables and fields for version changes too. Changing
capitalization alone cannot establish compatibility with a different schema.

Separate lexical normalization from version migration. Review every categorical
column used downstream for a shared normalization step before filters, joins,
recodes, and scoring. Lowercase/trimmed comparison keys must be applied to both
the data and the lookup values. If a project uses lowercase `snake_case` as its
internal convention, check it consistently across columns and modules. Preserve
source values and validate canonical output against the declared CLIF version.

Handle case, spacing, and punctuation variants only when the normalized key maps
unambiguously to a known category. Check for collisions where distinct categories
collapse to the same key, and surface unknown or ambiguous values. Do not apply
category normalization to identifiers, free text, column names, or filenames.
Lowercasing and replacing spaces cannot perform semantic renames such as
`High Flow NC` to `hfnc`. Those require a source-backed, version-scoped mapping.
Data migration remains a separate, deliberate step.

For each claimed version, use a small synthetic fixture with known qualifying
and nonqualifying rows. Check selection, joins/recodes, and the downstream
aggregate or score, including case/spacing variants, nulls, unknown values, and
normalization collisions. Equivalent lexical variants should yield the same
result under the documented normalization policy. If strict validation rejects
them, it must do so before computing a misleading metric. Verify that a
vocabulary mismatch cannot silently yield an empty cohort, all `other` labels,
or zero/normal scores. Also distinguish a legitimately empty cohort from a
broken filter. No real patient data is needed for these checks.

### Mortality regression case

Look for raw comparisons such as `discharge_category == "Expired"` in any
dashboard or analysis. In a synthetic cohort, verify these cases:

| Input | Expected behavior |
|-------|-------------------|
| `Expired`, `expired`, `EXPIRED`, ` Expired ` | The same death classification after normalization, or an explicit validation failure before mortality is computed. |
| Punctuation/spacing variant of a known category | Resolve only through an unambiguous normalized vocabulary lookup; detect collisions. |
| Native CLIF 3.0 `expired` | Death classification using the 3.0 vocabulary or a declared internal mapping. |
| `Died`, `Deceased` | Unmapped unless an explicit project decision supplies the alias; no guessed synonym mapping. |
| Nulls, unknown labels, and a truly zero-death cohort | Preserve missing/unknown status, distinguish mapping failure from a valid zero, and never invent deaths. |

When no deaths are counted, check for a visible data-quality warning and a
diagnostic of the cohort's discharge categories. Such output must follow the
project's suppression rules and the skill's PHI-safe output limits. Do not echo
arbitrary unknown/free-text labels, unsuppressed small cells, or patient rows
into shared diagnostics.
If a project uses an explicit death-definition configuration, check that it is
actually read and applied; a label added to an unused config does not fix a metric.
Apply the same review to every category-driven measure, not only mortality.

## macOS/Linux/Windows portability

Review the full documented path from installation to export. Check each item
where the project uses it; report a concrete failure scenario, not a generic nit.

- **Paths and working directories:** use `pathlib.Path`/`os.path.join` in Python
  or `file.path` in R. Find hardcoded home, drive, mount, `/tmp`, or separator
  assumptions, unexpanded `~`, relative paths tied to the launch directory, and
  unquoted paths with spaces. Check Windows drive/UNC paths, invalid filename
  characters such as timestamp colons, and temporary-file reopen/delete behavior.
- **Filename and import case:** compare every referenced filename, directory,
  module, and asset with its actual spelling. Common macOS/Windows filesystems
  can hide errors that Linux exposes. Case sensitivity depends on the filesystem;
  do not assume all Macs or Windows volumes behave alike. Case-only duplicate
  filenames can also prevent a usable checkout.
- **Shell and command dependencies:** distinguish Bash, POSIX sh, PowerShell,
  and cmd. Check BSD/GNU differences such as `sed -i`, `date`, and `readlink -f`,
  plus symlinks, executable bits, and shebangs. Prefer argument-list subprocess
  calls or standard-library operations where appropriate. Document required
  tools and shell-specific environment/activation commands. A `.sh` launcher
  or Unix hook is not evidence of native Windows support; WSL is a separate
  Linux execution environment and must be labeled as such.
- **Dependencies and architecture:** verify the declared Python/R versions,
  lockfiles, clifpy APIs, and binary/package availability for each claimed OS and
  architecture, including Apple Silicon where applicable. Flag compiled-library
  or system-tool requirements that installation instructions omit.
- **Processes and parallelism:** find fork-only assumptions, non-picklable
  workers, and missing Python `if __name__ == "__main__":` entry guards under
  spawn. Check R fork-based calls such as `mclapply` with multiple workers on
  Windows. Verify the runtime's actual start method rather than assuming it
  from the OS name.
- **Text, time, and outputs:** check UTF-8, CRLF/LF handling, locale-dependent
  CSV/number/date parsing, IANA timezone data availability, and DST conversions.
  Review output paths and serialized artifacts for the same portability issues
  as inputs. Line-ending differences are findings only when behavior breaks.

When execution is authorized and the environments are available, run the
documented entry command with synthetic data on each claimed OS. Include a
working directory/path with spaces and verify the expected aggregate output.
Static review and a successful macOS run do not prove Linux or Windows execution.

## Report coverage

For each finding, give the file/line, affected OS/version, a concrete trigger,
observed or source-demonstrated consequence, and a minimal fix. Label conditional
risks separately from confirmed failures. Do not report unsupported targets as
regressions when the project explicitly excludes them.

End with a matrix covering macOS, Linux, and Windows against CLIF 2.1 and 3.0.
For each cell, state **executed/pass**, **executed/fail**, **static review only**,
**not tested**, or **outside declared support**. Note WSL separately. Attach the
runtime/dependency versions, schema refs, commands, and synthetic assertions
for any executed checks. Never turn an unrun combination into a passing claim.
