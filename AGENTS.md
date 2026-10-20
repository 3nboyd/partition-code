# Repository maintenance

This repository builds Partition Code, a Codex coding configuration installer.
Read README.md, MODEL_MAP.md, ROUTING.md and SETUP_FOR_AGENTS.md. Keep changes
project-scoped and preserve unrelated instructions, configuration and working edits.
Run `python3 -m unittest discover -s tests -v` and `python3 scripts/check_public.py`.
Do not add memory, writing samples, credentials or private project history here.
When modifying roles, validate TOML schema, model/effort compatibility and argv
construction. Never reduce sandbox or approval controls to make tests pass.
