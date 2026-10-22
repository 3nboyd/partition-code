# Model map

Verified against official documentation and the installed Codex catalog on 2026-10-20.

```mermaid
flowchart TD
  User[Your coding request] --> Parent[Sol low: coordinate]
  Parent --> Simple[Simple task: handle directly]
  Parent --> Explore[Luna high: explore]
  Parent --> Small[Luna high: small edit]
  Parent --> Build[Sol medium: implement]
  Build --> Verify[Luna high: validate]
  Build --> Risk[Sol high: risky-change review]
  Parent --> Publish[Luna high: authorized publish]
```

Sol handles ambiguity and integration; Luna handles clear bounded work. Validation
is independent of implementation when useful. Review focuses on concrete risks.
This is a reasoned starting policy, not an empirical claim that these settings are
universally optimal. Compare actual success, latency and usage on your own tasks.
Avoid running six agents for a one-line fix.

The coordinator defaults to Sol / low. `--quality deep` selects Sol / high.
`--quality frontier` explicitly selects Astra / low for exceptionally difficult work.
Astra is never automatically launched by a role.

To customize an installed coding project:

1. Edit that project's `.relay/models.json` to change coordinator session policies.
2. Edit its `.codex/agents/relay_*.toml` files to change worker models and effort.
   These TOML files control workers; changing the `roles` summary in `models.json`
   does not rewrite them.
3. Run `python3 relay.py doctor --project /path/to/your/code --check-models` from
   this installer repository. Both the model and effort must be supported.

To change defaults for future installations, edit `models.json` and `agents/` in
this installer repository instead. Existing customized project files are preserved;
the installer refuses to overwrite local edits.

Run doctor after changes. A catalog listing does not prove account access. Update
retired model names rather than silently substituting one.

Sources: [Official model guidance](https://learn.chatgpt.com/docs/models),
[custom agents and model/effort precedence](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
