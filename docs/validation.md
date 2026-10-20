# Validation record

Checked 2026-10-20.

- 20 automated tests passed locally. CI repeats them on Python 3.11 and 3.13.
- Public tracked-tree audit passed, including checks for private/generated paths, credentials and machine-specific paths.
- A live signed-in Codex session launched a Sol coordinator, invoked the configured relay_explorer Luna worker, waited for its result and completed a read-only repository analysis.
- Installer lifecycle, ownership preservation, path guards, role schema, model validation and argument construction are covered.

These checks establish observed behavior, not a guarantee of perfect model judgments.
Review uncertain classifications, and use task-specific checks for generated work.

Mac launchers include tests for argument handling, existing-application preservation, and stopping on project conflicts. Native compilation is also checked in CI.

A review through Partition Code identified a cross-filesystem installer backup issue. Backup now supports that case and has a regression test.
