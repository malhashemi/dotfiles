# CLIProxyAPI runtime

This directory holds the running proxy's configuration, local subscription
credentials and Claude launch overrides. Shared installation inputs and portable
application preferences live in [`~/.config/ai-setup/`](../ai-setup/README.md).

| File | Purpose | Read by |
| --- | --- | --- |
| `config.yaml` | Proxy endpoint, upstream routing and gateway authentication | CLIProxyAPI service |
| `auth/` | Local subscription credentials | CLIProxyAPI service |
| `client-key` | This machine's gateway key | Setup and proxy helper |
| `claude-accounts.json` | Personal and Work account assignments | Account login helper and Mixed launcher |
| `claude-settings.json` | Private environment used to connect Claude to the local proxy | Claude launchers |
| `claude-context-settings.json` | Context budgets and related launch settings | Mixed launcher and first setup |
| `claude-model-defaults.json` | Generated from the catalog: Mixed family defaults and reviewed short-ID aliases. Routes are discovered live from `/v1/models` at each Mixed launch | Mixed launchers |
| `profiles.json` | Model defaults for the standalone `claude-openai`, `claude-grok` and `claude-multi` wrappers | Proxy launcher |
| `claude-session-*.json`, if present | Generated per-configuration settings for those standalone wrappers | The corresponding Claude session |

T3 does not store its preferences here. Its files are under `~/.t3/userdata/`;
the [AI setup guide](../ai-setup/README.md) maps the portable inputs to those files
and explains the preview/apply commands.

Both Mixed profiles share `~/.claude/settings.json` and `~/.claude/CLAUDE.md`.
Their launcher adds the selected account, proxy connection and context settings
when starting Claude. Updates to launcher inputs take effect in new sessions.

At each new Mixed session the launcher asks this proxy for `/v1/models` with the
local `client-key` (loopback only, no redirects) and keeps only the selected
account's `claude-a/` or `claude-b/` Claude models. Each bare ID is routed to that
account's exact ID through `modelOverrides`, and the launch model and family
defaults are rewritten to it. A model the proxy advertises is routable without a
catalog change. If the proxy is down, returns a malformed list, advertises nothing
for that account, or a requested Claude ID is not advertised for it, the launch
stops with an error; it never falls back to the other account or an unprefixed
route. A leftover `claude-model-routes.json` from earlier versions is no longer read.

```sh
cpapi status
cpapi models
cpapi login personal
cpapi login work
cpapi login openai
cpapi login grok
```

For re-authentication, use `cpapi login personal` or `cpapi login work` again and
select the matching account/workspace. These helpers preserve the registered
filename and restore the `claude-a` or `claude-b` routing prefix. Avoid raw
`cliproxyapi -claude-login` for these named profiles: it can create a separate,
unprefixed email-named credential. Do not copy that over a registered profile file;
losing its prefix breaks the routes that OpenCode and T3 expect. Check `cpapi models`
after login for the selected profile's prefixed models.

Use `cpapi start`, `cpapi stop` or `cpapi restart` to manage the proxy service.
Logins remain local to each machine. Never commit this whole directory: it
contains credentials and gateway keys. Chezmoi tracks only the selected public
definitions and this guide.

Historical setup notes, proposals and verification output are archived under
`~/.local/share/claude-archives/`. Generated session files can be recreated by
their launcher; keep them while a session using them is running.
