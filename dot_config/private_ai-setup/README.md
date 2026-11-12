# Local AI setup

`ai-setup` provisions the shared Claude/Codex/Grok preferences, hook venv,
CLIProxyAPI, T3 installation, service units and Tailscale access. `--install`
retains those responsibilities; `--update-plan` previews explicit upgrades.
No upgrade is needed for this migration.

Claude uses one local CLIProxyAPI pool. T3 uses built-in `claudeAgent`, binary
`claude`, blank `homePath`, empty provider environment, native model discovery,
and Opus 5.5 at high effort. Terminal Claude shares this pool through the
private `env` in normal `~/.claude/settings.json`. Hooks, skills, MCP, project
trust, and transcripts remain in their normal homes. The retired alternate
home is left on disk; no history database is rewritten.

Routing is fill-first with personal 300, work 200, backup 100, session affinity
720h, subagent inheritance and persisted cooldowns. Bare model IDs use the
pool. Existing optional prefixes remain diagnostic routes. T3 load balancing
is off. Native Codex/Grok and OpenCode OpenAI remain independent.

## Targeted rollout

Deploy source-managed inputs and binaries with scripts excluded. Existing
machines' run-once setup also refuses automatic installation and prints the
migration command. Do not use `--install` to migrate an existing machine.

1. Review `ai-setup --pool-diff` (read-only; secrets are never printed).
2. Arrange a brief proxy maintenance window. The operator must stop its managed
   supervisor and exclude concurrent starts, raw OAuth writers and refreshers.
   The helper never stops/restarts anything. T3 may remain open during this phase.
3. If duplicate tokens differ, explicitly choose the canonical credential after
   checking identity; never infer freshness from file modification times:
   `cpapi --proxy-stopped reconcile work claude-account-b.json` (use the actual
   registered canonical filename). Other same-identity credentials move to private
   `archive/`, outside watched `auth/`, with inventory quarantine records. A private
   reconciliation journal rolls forward after interruptions; rerun the account
   command before starting the proxy. No token is copied over the canonical file.
4. While the proxy remains stopped, run
   `ai-setup --proxy-stopped --apply-pool-accounts`. Metadata reads the latest
   on-disk credential and atomically merges priority/disabled only. Upstream v8.0.20
   live fields/status PATCH snapshots can overwrite refreshed tokens; they are not
   used. Process/endpoint checks detect mistakes; they cannot exclude a concurrent
   start. Operator-controlled maintenance is the safety boundary.
5. Run `ai-setup --apply-pool-config`. It requires verified account metadata,
   preserves unrelated configuration, and backs up replacements under
   `~/.local/share/ai-setup-backups`. It updates proxy/Claude configuration only;
   T3 may stay running. Resume the proxy using its existing supervisor separately.
6. For live T3, run `ai-setup --export-pool-t3-patch /PRIVATE/NEW-PATH.json`.
   The exclusive mode-0600 export contains `serverSettingsPatch` and
   `clientSettingsPatch`; model favorites/menu are also patched on the server
   which owns them in T3 0.1.1. The export is secret-bearing and must never be printed or logged.
   The rollout owner applies it through T3's authenticated supported settings
   APIs (server RPC `server.updateSettings`, payload `{patch: serverSettingsPatch}`),
   re-reading current settings before applying map replacements. The helper does
   not create an unauthenticated API or attempt authentication. Remove the private
   export after use. Alternatively, close T3 normally and run
   `ai-setup --apply-pool-t3-offline`; this fallback checks the server and desktop
   are closed before writing their files. Only this T3 file phase requires closure.
7. Verify native Claude, the local usage hub, and Fleet doctor without inference.
   Repeated account/config/offline-T3 phases are idempotent. The combined legacy
   `--proxy-stopped --apply-pool-changes` requires both proxy and T3 stopped.

These commands do not install packages, invoke inference, restart services or
rewrite histories. Private machine-local management keys stay loopback-only.
The config reader supports JSON-compatible YAML, including legacy top-level and
v8 nested `server`, `access`, and `oauth` fields. Arbitrary YAML is not supported;
convert it privately to equivalent JSON before using these helpers.

## Accounts

Generic policy lives in `bootstrap.json` and `models.json`. Mutable account
state lives in private `~/.config/cli-proxy-api/accounts.json`; auth files,
client key, management key and inventory are excluded from chezmoi. Setup seeds
personal/work/backup only when inventory is absent. Backup is pending and
optional until login. Removed records are tombstones and never re-seeded.

```
cpapi list
cpapi --proxy-stopped login personal -no-browser
cpapi --proxy-stopped login work -no-browser
cpapi login backup -no-browser
cpapi add second-openai codex --priority 50
cpapi login second-openai
cpapi add second-grok xai --priority 25
cpapi login second-grok
cpapi --proxy-stopped priority backup 400
cpapi --proxy-stopped disable backup
cpapi --proxy-stopped enable backup
cpapi --proxy-stopped remove backup
```

Providers `openai` and `grok` alias `codex` and `xai`; legacy `claude-a/b`
alias personal/work. OAuth runs in an isolated auth directory, validates stable
identity and tokens, rejects duplicate identities, and keeps the registered
filename on refresh. Login never edits T3. Remove disables and archives the
inventory record without deleting tokens. Use `cpapi --proxy-stopped restore NAME` to reactivate retained credentials,
or re-add the same removed name and login again. Removed/quarantined identities
are not active collisions; another active account's identity is protected.
Newly added accounts are optional pending login, then required on activation.
Adding a pending account and its first login can run while the proxy is up:
the staged credential is published exclusively and never replaces an existing
file. Changes to existing credentials, including relogin, require the
proxy-stopped maintenance boundary above. OAuth staging overrides both legacy
and v8 auth-dir fields.

OpenCode uses `claude/claude-opus-5-5#high` and bare wire model IDs. Its local
compatibility plugin keeps stripping unsupported thinking block_binding and
its beta header. Existing threads using old Claude logical provider IDs may
need manual model selection; no history rewrite is performed.

Other setup commands remain available: `--cli-diff`, `--apply-cli-changes`,
`--apply-claude-hooks`, `--t3-diff`, `--apply-t3-changes`, `--proxy-diff`,
`--apply-proxy-changes`, `--connections`, `--update-plan`, `--update-tools`.
T3 file preference merges require T3 closed; use the targeted pool action when
only migrating the pool. CLI preference merge installs the hook venv; the
pool action does not.

## Directory map

This directory contains installation and preference inputs. Applications do not
read it directly: `ai-setup` reads these files and merges selected values
into each application's own settings. There is no background synchronization.

| File | Purpose | Used when |
| --- | --- | --- |
| `models.json` | Shared model choices, reasoning effort and Codex service tier | CLI and T3 preference merges |
| `cli-preferences.json` | Shared Claude and Grok preferences | CLI preference merge |
| `t3/preferences.json` | Shared server, desktop, browser and model-menu preferences | T3 preference merge |
| `t3/profiles.json` | Native provider definitions | T3 preference merge |
| `t3/keybindings.json` | Shared shortcuts with platform-specific modifiers | T3 preference merge |
| `bootstrap.json` | Seed configuration for a new proxy and fallback T3 CLI version | Installation |
| `proxy-headers.json` | Explicit provider header overrides; `null` removes a managed header | Installation or proxy header merge |
| `machine.json` | This machine's role, hosts and remote-access choices, rendered from local chezmoi answers | Setup and connection commands |
| `deployment-targets.json` | Explicit file list for a targeted AI setup rollout | Deployment planning |

### Where the effective settings live

Paths below are relative to each machine's home directory.

| Application | Files it actually reads |
| --- | --- |
| Claude | `~/.claude/settings.json` and `~/.claude/CLAUDE.md` |
| Codex | `~/.codex/config.toml` |
| Grok | `~/.grok/config.toml` |
| T3 server: providers, models, title/Git-text generation and server behavior | `~/.t3/userdata/settings.json` |
| T3 desktop preferences | `~/.t3/userdata/client-settings.json` |
| T3 keyboard shortcuts | `~/.t3/userdata/keybindings.json` |
| T3 window and desktop connection settings | `~/.t3/userdata/desktop-settings.json`; window geometry stays local |
| CLIProxyAPI and its launchers | `~/.config/cli-proxy-api/`; see its [runtime guide](../cli-proxy-api/README.md) |

Edit the chezmoi source for portable changes, then deploy only the relevant input
files and helper. Preview with `ai-setup --cli-diff` or `--t3-diff`, then
use the corresponding `--apply-cli-changes` or `--apply-t3-changes`. Updating an
input file alone does not change an existing app's settings. Close T3 before
applying its preferences; start new CLI sessions to use updated defaults.
Direct changes inside an app stay local until deliberately captured in these
portable inputs. A later preference merge reapplies the selected shared keys.

The helper is `~/.local/bin/ai-setup`. The proxy directory holds live
connection settings and credentials, while private historical backups belong
under `~/.local/share/claude-archives/`, outside the public dotfiles repository.


## Installation inputs

`chezmoi init` asks once for:

- Machine role: `laptop`, `desktop`, or `headless`. The existing `is_headless`
  value supplies a migration default; the chosen role replaces hostname guesses.
- Whether to install the shared AI setup.
- Tailscale usage and whether to enable T3 remote access through Tailscale HTTPS.
- Optional Bitwarden import, SSH username, and any missing hostnames.

The public template is `.chezmoi.toml.tmpl`. Answers live in the machine's
`~/.config/chezmoi/chezmoi.toml`; the generated
`~/.config/ai-setup/machine.json` passes only required machine configuration
to the setup helper. Changes to these local values do not require editing the
public repository. To change a saved answer, use `chezmoi edit-config`, then
preview the affected targets. To ask again for a particular imported value,
remove that local key and rerun `chezmoi init`.

The SSH template uses the saved SSH username and omits aliases with blank hosts.
On an existing machine, review `chezmoi diff ~/.ssh/config` separately before
applying it; the AI-only target list leaves the current SSH configuration alone.

Disabling AI setup excludes its managed targets and skips its install hook.
It does not uninstall packages or delete an existing working setup.

## Bitwarden

Reuse the existing `dotfiles-secrets` item (or choose a different item name/ID).
Add the following **custom fields**, including on a Secure Note item:

| Field | Value |
| --- | --- |
| `T3_DEV_HUB_HOST` | Headless host's Tailscale FQDN or IPv4 address |
| `T3_ARCH_DESKTOP_HOST` | Arch desktop's Tailscale FQDN or IPv4 address |
| `T3_MAC_WORKSTATION_HOST` | Laptop's Tailscale FQDN or IPv4 address |
| `T3_SSH_USER` | SSH username shared by the machines |

A fully qualified Tailscale hostname is preferable for an HTTPS Remote link.
A bare IP or short hostname still works as an SSH target, but use the server's
advertised HTTPS hostname for phone/Remote link pairing.

The existing `secrets` command exports custom fields as environment variables.
The new init template can also read these four fields directly through chezmoi's
`bitwardenFields`. It never imports arbitrary fields or API tokens into template
data. Only these machine-details fields are accepted.

For a first direct vault import, install `bw` if necessary and log in/unlock it
in the same shell before `chezmoi init`. For example, in bash or zsh:

```sh
bw login                         # only if not already signed in
export BW_SESSION="$(bw unlock --raw)"
bw sync
chezmoi init
unset BW_SESSION
```

The init template does not install packages or unlock the vault itself. If `bw`
is missing or locked, it explains that and uses ordinary prompts instead. The
existing OS bootstrap installs `bw`, so this is not a requirement for completing
the rest of a fresh installation. An ambiguous item name or failed vault lookup
stops init; use the item's ID or choose manual prompts after resolving it.

Value precedence is: **saved local answer, supplied environment variable,
Bitwarden field, interactive prompt**. Saved values are not silently refreshed
from the vault. Later init runs with complete local answers do not access it.

Reusable API secrets for unrelated tools can continue using `secrets`. This
subscription setup requires no OpenAI/xAI API key. The setup helper reads its
local JSON explicitly; services and desktop launches do not depend on shell
startup files or an unlocked Bitwarden vault.

`private_` in a chezmoi source filename restricts target file permissions; it
does not encrypt the source or conceal it from Git. Never commit raw secrets,
OAuth files, pairing codes, generated connection catalogs, or application state.


## T3 service layout

The proxy listens on `127.0.0.1:8317`. Each machine generates its own gateway key.
The T3 service listens on loopback only: the helper creates
`~/.t3/service.env` with `T3CODE_HOST=127.0.0.1` (from T3 0.1.5 a service
otherwise listens on every private network, LAN included). Tailscale Serve
supplies HTTPS for remote clients, and other machines' T3 apps reach it over
SSH as an existing server. An existing `service.env` is left alone; a new one
takes effect at the next `t3 service restart`.

Only one T3 server can use a T3 home. On an agent desktop the service owns
`~/.t3`, so the helper turns off the desktop app's local environment
(`localEnvironmentEnabled: false` in `desktop-settings.json`) and the app
connects to the service like any other environment: pair it once with
`t3 pair --label "This desktop"` and open the printed `t3code://pair` link on
that desktop. The service is installed with the setup-owned CLI, whose version
follows the installed desktop app, so app and service match. An existing T3
server that is not the service (for example one another machine's app started
over SSH) must be stopped before the first install; threads and settings in
`~/.t3/userdata` carry over. Desktop exposure is managed through selected T3 settings. This
package never enables public Tailscale Funnel.


## Remote environments and phone access

```sh
ai-setup --connections
```

This displays the other hosts and the saved SSH username. Add them in T3's
Connections screen. Remote link uses the advertised HTTPS address and a fresh
pairing code from the target host:

```sh
t3 auth pairing create --label "Arch desktop" --ttl 5m
```

Use a device-specific label such as `Mac laptop`, `Arch desktop`, or `Phone`.
A desktop app lists the other two hosts; the phone can list all three. A headless
server has no desktop app with an outgoing environment list. Each connecting
client gets its own local authorization, including the server's own desktop app.

Remote link reuses its saved authorization. T3 0.0.40 SSH bootstraps can leave old
unnamed sessions after reconnecting. Review client names/connection status before
revoking duplicates. The installer never revokes or recreates existing pairings.

The host inventory is portable; encrypted connection catalogs and authorizations
remain in each app's local storage. Copying those files between machines is not
part of setup.

## References

- [chezmoi init prompts](https://www.chezmoi.io/user-guide/setup/)
- [chezmoi Bitwarden integration](https://www.chezmoi.io/user-guide/password-managers/bitwarden/)
- [CLIProxyAPI installation](https://github.com/router-for-me/CLIProxyAPIDocs/blob/main/docs/en/introduction/quick-start.md)
- [T3 background service](https://github.com/pingdotgg/t3code/blob/main/docs/user/background-service.md)
- [T3 remote access](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md)
- [Grok Build installation](https://docs.x.ai/build/overview)
