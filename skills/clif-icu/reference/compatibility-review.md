# CLIF code compatibility review

Use when writing, debugging, or reviewing CLIF analytics in R or Python. Apply
the same checks in any coding harness. Use synthetic data only.

## Category and schema bugs

- Confirm the CLIF data version and installed library versions. A version flag
  declares intent; it does not validate data or migrate it.
- Retrieve the matching [current mCIDE and schemas](current-mcide.md). Check
  table/column names and category/group/type values in filters, joins, recodes,
  pivots, and scoring constants.
- Validate required fields, key types, and join cardinality before analysis.
  Repair nonconforming headers only with an explicit schema-backed rename map;
  check collisions and never silently drop required columns or unmatched rows.
- Check case, surrounding whitespace, punctuation, and `snake_case` on both
  data and lookup keys. Normalize categorical comparison keys consistently,
  preserve source values and nulls, and detect ambiguous normalization collisions.
- Do not lowercase identifiers, free text, filenames, or all column names as a
  blanket fix. Normalization is not a version crosswalk: `IMV` becomes `imv`,
  but `High Flow NC` becomes `hfnc`, not `high_flow_nc`.
- Use explicit, version-scoped mappings for renamed values. Report unknown
  categories instead of silently turning them into `other`, false, or zero.
- Audit and normalize before category filtering or predicate pushdown can
  discard nonconforming rows. Preserve evidence of unknowns and collisions.
- Exercise mixed case, spaces, underscores, nulls, unknowns, and a known
  qualifying row with synthetic fixtures. Verify downstream results, not only
  that code runs. Distinguish a legitimately empty result from a broken filter.

## macOS, Linux, and Windows

- Build paths with Python `pathlib` or R `file.path`. Check working-directory,
  drive/UNC, temporary-file, spaces-in-path, and invalid-filename assumptions.
- Check exact filename/import case and case-only duplicates. Filesystem case
  sensitivity varies; a successful macOS/Windows read can hide a Linux failure.
- Match commands to Bash/Zsh, PowerShell, or cmd. Check BSD/GNU flags, CRLF,
  executable bits, symlinks, and shell-specific environment/activation syntax.
  A Bash-only helper needs a documented shell; WSL is separate from native Windows.
- Verify package/runtime versions and native dependencies for the target OS and
  architecture. Check Python spawn/pickling/entry guards and R fork-only workers.
- Check UTF-8, locale-sensitive parsing, timezone data, DST, and export paths.

## Review evidence

Give each finding a file/line, concrete failing input, affected version/OS,
consequence, and minimal fix. Report macOS/Linux/Windows coverage for each declared
CLIF version, including 2.1/3.0 or future targets, as executed/pass, executed/fail,
static only, untested, or outside declared support.
Do not certify a harness, model, or OS from a run on another environment.
