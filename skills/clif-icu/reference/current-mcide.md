# Retrieve current CLIF knowledge

Use public sources only. Never put patient values, identifiers, logs, local
configurations, or secrets into MCP queries, web searches, or GitHub requests.

1. Read the study's declared CLIF version. Check the official
   [CLIF releases](https://github.com/Common-Longitudinal-ICU-data-Format/CLIF/releases)
   and [change log](https://clif-icu.com/data-dictionary/change-log). Do not
   upgrade a study because a newer release or development branch exists.
2. Use an available GitHub MCP tool to list the repository's `mCIDE/` directory
   at the matching tag or maintained version branch. Discover paths instead of
   guessing filenames. Resolve a moving branch/tag to a commit SHA before reuse.
   Without MCP, use GitHub's contents API or a read-only Git checkout.
3. Fetch only the needed vocabulary CSVs and schema/documentation files at that
   SHA. Record repository, ref, commit SHA, retrieval date, and library version.
   The API form is `repos/{owner}/{repo}/contents/{path}?ref={sha}`.
4. Compare canonical category columns with the target version's data dictionary
   and installed library schema. Example/name columns are not permissible-value
   lists. If sources disagree, show the discrepancy; do not invent a conversion.
5. Keep analysis dependencies and vocabulary snapshots reproducible. Check live
   sources again for a new task or explicit refresh. Offline, identify the cached
   ref/date and mark freshness unverified; do not silently fall back to memory.

The data standard is [CLIF](https://github.com/Common-Longitudinal-ICU-data-Format/CLIF);
the Python implementation is [clifpy](https://github.com/Common-Longitudinal-ICU-data-Format/clifpy).
Their version numbers are independent. Bundled references are snapshots, not a
live authority. Check actual installed signatures before generating API calls.

For example, the CLIF 2.1 respiratory vocabulary contains `IMV` and `High Flow NC`;
3.0 uses `imv` and `hfnc`. The active 3.0 branch can evolve beyond a release tag
or installed clifpy schema. Inspect the selected ref rather than copying an old list.
