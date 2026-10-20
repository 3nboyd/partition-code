# Partition Code

Partition Code adds model-specific coding agents to Codex. A coordinator assigns
focused work to an explorer, implementer, validator, or reviewer, then brings the
results back into one conversation. Small fixes usually stay with the coordinator.

The project grew out of a recurring question: which model is worth using for this
particular task? The setup takes inspiration from
[subagents_configs](https://github.com/nsEytgXm/subagents_configs), with its own
routing rules and project-scoped installer. Writing references are handled separately
by [Partition Writing](https://github.com/3nboyd/partition-writing).

## Get started

Requires Python 3.11+, Git, and Codex CLI. Sign in with `codex login`, then run:

```sh
git clone https://github.com/3nboyd/partition-code.git
cd partition-code
python3 relay.py install --project /path/to/your/code
python3 relay.py doctor --project /path/to/your/code --check-models
python3 relay.py run --project /path/to/your/code
```

Ask for the change, investigation, or review in the session that opens. The launcher
registers the project agents and applies the model settings without changing global
Codex configuration. Existing chats may need to be restarted to discover new agents.

### On a Mac

Run `python3 install_macos.py` to add **Partition Code** to your Applications folder.
This requires Apple Command Line Tools (`xcode-select --install`). Open the app,
choose a coding folder, and continue in the Terminal session it starts. The launcher
installs the project agents first and preserves conflicting files.

Keep the cloned repository in place; the launcher uses that copy.

## Model map

| Work | Role | Model / effort |
| --- | --- | --- |
| Planning and integration | Coordinator | GPT-6.1 Sol / low |
| Repository discovery | relay_explorer | GPT-6 Luna / high |
| Small, clear edits | relay_quick | GPT-6 Luna / high |
| Larger features and fixes | relay_implementer | GPT-6.1 Sol / medium |
| Independent checks | relay_validator | GPT-6 Luna / high |
| Changes needing closer review | relay_reviewer | GPT-6.1 Sol / high |
| Authorized commits and pushes | relay_publisher | GPT-6 Luna / high |

These are starting defaults. [MODEL_MAP.md](MODEL_MAP.md) explains the choices and
how to change them; [ROUTING.md](ROUTING.md) describes when each role is useful.
The launcher allows two workers at once. Workers share the checkout and inherit
the parent session's permissions, so file ownership still matters.

## Common commands

```sh
python3 relay.py run --project /path/to/code --read-only "Analyze the authentication flow"
python3 relay.py run --project /path/to/code --quality deep "Investigate this intermittent failure"
python3 relay.py run --project /path/to/code --dry-run "Explain the test failure"
python3 relay.py run --project /path/to/code --exec "Fix the parser and run its tests"
python3 relay.py uninstall --project /path/to/code
```

`--read-only` applies to the whole session. `--quality deep` increases the
coordinator's reasoning effort; `frontier` explicitly selects Astra. Worker
models are configured separately in their TOML files.

The installer adds a section to AGENTS.md and files under `.relay/` and
`.codex/agents/`. It preserves unrelated configuration and modified managed files.
Uninstall removes its own files and retains local edits.

Codex access and usage limits come from the signed-in account. This project
currently supports Codex. [SETUP_FOR_AGENTS.md](SETUP_FOR_AGENTS.md) provides
instructions for another assistant setting it up.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_public.py
```

CI runs on Python 3.11 and 3.13. Mac launcher compilation is checked on macOS.
