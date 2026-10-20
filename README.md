# Partition Code

A small, inspectable coding orchestrator for Codex. One coordinator chooses focused
specialists with different models; you keep one conversation and one final answer.
Inspired by the workflow in [subagents_configs](https://github.com/nsEytgXm/subagents_configs),
with an independent implementation, conservative concurrency, and current model settings.
The separate [Partition Writing](https://github.com/3nboyd/partition-writing) project
handles writing samples and personal context. This repository contains no personal library.

## Setup

Requires Python 3.11+, Git, and a recent Codex CLI signed in with `codex login`.
Use the installer from this cloned repository and point it at your coding project:

```sh
git clone https://github.com/3nboyd/partition-code.git
cd partition-code
python3 relay.py install --project /path/to/your/code
python3 relay.py doctor --project /path/to/your/code --check-models
python3 relay.py run --project /path/to/your/code
```

Tell it what you want built, fixed, analyzed or reviewed. The launcher explicitly
registers project roles for that session, including before project configuration is
trusted. It leaves global Codex settings alone. In the desktop app, open the target
repository and start a fresh chat; project agents also live in `.codex/agents/`.
Use the CLI launcher when you need its explicit model and concurrency settings.

```sh
python3 relay.py run --project /path/to/code --read-only "Analyze the authentication flow"
python3 relay.py run --project /path/to/code --quality deep "Debug this intermittent race"
python3 relay.py run --project /path/to/code --dry-run "Explain the test failure"
python3 relay.py run --project /path/to/code --exec "Fix the parser and run its tests"
python3 relay.py uninstall --project /path/to/code
```

The installer adds a bounded block to AGENTS.md and project-scoped `.relay/` and
`.codex/agents/` files. It refuses to overwrite unrelated or modified managed files.
It does not edit an existing `.codex/config.toml`, trust settings, or global prompts.
Uninstall retains modified role files and removes its own instruction block.

## Routing

| Work | Role | Model / effort |
| --- | --- | --- |
| Scope and integration | Coordinator | GPT-6.1 Sol / low |
| Repository discovery | relay_explorer | GPT-6 Luna / high |
| Small, clear edits | relay_quick | GPT-6 Luna / high |
| Nontrivial implementation | relay_implementer | GPT-6.1 Sol / medium |
| Independent checks | relay_validator | GPT-6 Luna / high |
| Risky change review | relay_reviewer | GPT-6.1 Sol / high |
| Authorized Git publishing | relay_publisher | GPT-6 Luna / high |

See [MODEL_MAP.md](MODEL_MAP.md) for rationale and overrides and [ROUTING.md](ROUTING.md)
for exact delegation contracts. Simple work stays with the coordinator. At most two
workers run concurrently through the launcher. Workers share the checkout and inherit
the parent's permissions. Read-only role prose is not an independent sandbox;
`--read-only` sets the parent filesystem sandbox. External tools have their own controls.

Your signed-in plan's Codex access and limits apply. This does not grant extra model
entitlements, API credit, ChatGPT memory, or other providers. No API key is required
for supported ChatGPT sign-in. Main-model selection occurs at session start; role
routing selects worker models, not a hidden mid-turn coordinator swap.

## For another AI

Read [SETUP_FOR_AGENTS.md](SETUP_FOR_AGENTS.md), then install and run doctor. Do not
publish credentials, sample libraries, or user conversation history. This project
supports Codex; it does not claim untested OpenCode provider or authentication compatibility.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_public.py
```

CI runs on Python 3.11 and 3.13. Model catalog checks validate client configuration,
not account entitlement or a benchmark proving one model is best for every task.
