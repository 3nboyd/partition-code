# Setup contract for an AI assistant

1. Read README.md and MODEL_MAP.md. Identify the user's target coding directory.
2. Verify Python >=3.11 and `codex --version`. If sign-in is missing, instruct the
   human to run `codex login`; never read or copy authentication files.
3. Inspect target AGENTS.md, AGENTS.override.md, .codex and working changes.
4. Run `python3 /absolute/path/to/partition-code/relay.py install --project TARGET`.
   Conflicts preserve user files. Reconcile only the named conflict within authorization.
5. Run doctor with `--check-models`. Missing/retired models require an available model
   with a supported effort; do not invent entitlement. Do not bypass host trust controls.
6. Run `run --dry-run` and show the model, sandbox and intended paths if requested.
7. Launch `run --project TARGET` or open the repository in Codex. Explain that an
   already-open chat may need a fresh session to discover roles.

Use `--read-only` for analysis-only sessions. `--exec` is a single noninteractive task.
Do not launch publisher without human authorization. Installer and run arguments
are ordinary argv; never interpolate user prompts into shell commands.
