# Adding or replacing a model

Use this guide when a model becomes available through an existing OpenAI,
Anthropic, or Grok subscription. Adding it to the catalog makes it selectable;
promoting it to a default is a separate decision. Work in the chezmoi source,
then review and deploy only the relevant targets.

## 1. Confirm compatibility and account access

- Record the exact upstream model ID, supported effort levels, tool support,
  context/output limits, and the versions of CLIProxyAPI and the provider CLI
  needed to use it. Use current provider documentation and release notes.
- Verify access through the subscription endpoint on each execution host. API
  availability or a published API context limit does not establish subscription
  access. For Anthropic, check Personal and Work separately.
- Inspect `cpapi status` and `cpapi models`, then verify a real request through
  the Mixed launcher. A listing or an alias alone does not prove the route works.
- Check native T3 providers separately from the Mixed Claude provider. Native
  Codex/Grok use their own CLI authentication stores.
- If versions need updating, preview `claude-mixed-setup --update-plan` and
  schedule maintenance. `--update-tools` is explicit; Arch maintenance includes
  a full system upgrade. Do not upgrade or restart during active workflows.

Keep model identities honest. Never make an old model ID silently call a new
model or another family. Sonnet and Haiku retain their real routes; their use
remains prohibited by the shared instructions.

## 2. Edit the portable catalog

The source is `dot_config/private_ai-setup/models.json`; the installed copy is
`~/.config/ai-setup/models.json`.

| Field | Purpose |
| --- | --- |
| `catalog[].id` | Exact model ID used by Claude workers and model selectors |
| `catalog[].name` | Human-readable label |
| `catalog[].provider` | `claude`, `codex`, or `grok` |
| `catalog[].t3Custom` | Set to `true` to add a T3 custom entry in both Mixed profiles |
| `catalog[].efforts` | Ordered supported effort options for that custom entry |
| `catalog[].pickerSuffix` | Optional Claude picker suffix; use `[1m]` only when verified |
| `effort` | Preferred effort by model ID; for a custom entry it must occur in `efforts` |
| `providers` | Explicit default model for each provider |
| `claudeFamilyDefaults` | Separate Fable, Opus, Sonnet, and Haiku family alias targets |
| `additionalClaudeRoutes` | Anthropic identities kept routable outside the picker lineup |
| `t3` | Provider used for conversation, title, and Git-text defaults |

Keep catalog IDs unique. Add a preferred effort for each new model. Catalog
order controls the Claude picker and the generated T3 custom entries; T3's
explicit menu ordering is maintained separately. Existing effort labels are
preserved; a new level uses its capitalized name unless its label is added to
the profiles template.

Chezmoi templates derive these files from the catalog:

- `~/.config/ai-setup/t3/profiles.json`: Personal and Work custom entries,
  effort options, and family aliases.
- `~/.config/cli-proxy-api/claude-model-routes.json`: current and retained
  Anthropic model identities. The launcher adds the selected account prefix.
- `~/.config/cli-proxy-api/claude-context-settings.json`: Claude picker entries.
- `~/.config/cli-proxy-api/profiles.json`: standalone OpenAI/Grok wrapper defaults.

Applications continue to read the generated JSON files. Edit their source
catalog/templates, not those generated copies. Ordinary catalog additions do
not require editing CLIProxyAPI's private `config.yaml`. If a release requires
new proxy configuration, review a targeted merge separately; `bootstrap.json`
seeds new installations and does not update an existing private configuration.

## 3. Review context and deliberate model choices

The current context template declares a shared 500K custom-model budget and
disables gateway discovery. The current Anthropic picker entries use `[1m]`.
`planned_cli()` in `claude-mixed-setup` also appends `[1m]` to the global Claude
default. These are existing choices, not guarantees for a newly released model.

Check how the installed Claude version interprets the exact ID and suffix,
reserve output/tool-result headroom, and verify compaction and delegation from
a long parent session. A model needing a different budget may require an
additional reviewed change: this catalog does not provide per-worker context
budgets. Server-side compaction is a separate integration capability; adding a
model does not enable it. Leave standalone Codex context overrides untouched
unless explicitly requested.

Review these independently when promoting or retiring a model:

- `dot_claude/CLAUDE.md`: effort-specific ratings and model preferences. Use
  benchmark evidence, including effort/cost comparisons, and the owner's actual
  experience. Cost efficiency means useful work within subscription allowances.
  Personal and Work already share this file. Preserve the Notes section and the
  requirement for primary reviews to cross Anthropic and OpenAI.
- `dot_config/private_ai-setup/t3/preferences.json`: menu order, favorites, and
  hidden models. Adding a catalog entry does not update these lists.
- The saved specialists and `mixed-review.js` under
  `private_dot_claude-t3-mixed/`: explicit model and effort choices are independent
  of the catalog defaults.
- `dot_claude/skills/codex-computer-use/SKILL.md`: change its pinned model only if
  intended, retaining its tool-access guidance and other settings.

Removing a catalog entry does not remove a saved T3 custom entry: the merge
preserves extra local models and favorites. Review retirement separately, keep
old IDs honest for existing sessions, and use an explicit removal or hiding
change when desired.

## 4. Preview and validate

For a refactor, render each affected template with `chezmoi execute-template
--file <source-template>` and compare parsed JSON with the previous output.
For a model addition, inspect the intended differences instead. Check both
account prefixes, effort options/defaults, picker entries, and preserved routes.
Validate the helper's proposed CLI/T3 merges for fresh and existing settings.
Keep temporary checks and fixtures outside the public dotfiles repository.

Before fleet rollout, verify one host with a fresh Mixed session, a native Agent or
Workflow worker, and the selected effort. Verify account-specific Anthropic
routing and the relevant context behavior. Repeat availability checks on the
other execution hosts; subscription rollout timing may differ.

## 5. Commit and distribute deliberately

1. Review the source diff and commit the catalog, templates, guidance, and any
   intentional preference changes together. Push the reviewed commit.
2. Pull the same commit on each intended host without overwriting local edits.
3. Select only the affected target paths from `deployment-targets.json`. For a
   model-only update, use the smaller changed subset. Preview with
   `chezmoi diff --exclude=scripts <targets...>` and apply with
   `chezmoi apply --exclude=scripts <targets...>`. Never run a broad apply or a
   command that combines pulling with an unreviewed apply.
4. Deploy updated inputs and any changed helper together. Input deployment does
   not itself merge existing T3 or CLI preferences. Preview `--cli-diff` and
   `--t3-diff` with `claude-mixed-setup`. These previews cover all selected shared
   preferences, so stop and isolate unrelated drift before applying.
5. For additions only, preview `--t3-diff --models-only` and apply with
   `--apply-t3-changes --models-only`. T3 reloads the watched server settings
   without restarting active sessions; existing model options and client menus
   are preserved. For a full preference merge, finish active work and close
   the T3 desktop or stop the headless T3 service.
   Apply the reviewed merges with `--apply-cli-changes` and/or
   `--apply-t3-changes`. Restart only affected services and open fresh sessions.
6. Check the model and effort on the laptop, Arch desktop, and dev-hub. A phone
   uses the selected execution environment and needs no local proxy install.

Credentials, gateway keys, subscriptions, and pairing records stay local. No
new login is normally needed merely to add a model to an already-authorized
provider; handle any actual entitlement or expired-login issue on that host.
Keep the helper's private backups and the previous source commit for rollback.
For rollback, restore only affected inputs and settings; preserve unrelated
local changes and any newly created credentials.

## References

- [CLIProxyAPI configuration](https://github.com/router-for-me/CLIProxyAPI/blob/main/config.example.yaml)
- [Claude Code model configuration](https://code.claude.com/docs/en/model-config)
- [OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Chezmoi templates](https://www.chezmoi.io/user-guide/templating/)

Consult current documentation when a model is released; this guide intentionally
does not pin future model capabilities or package versions.
