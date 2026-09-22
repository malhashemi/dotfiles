# Shared AI setup: macOS and Arch Linux

## Directory map

This directory contains installation and preference inputs. Applications do not
read it directly: `claude-mixed-setup` reads these files and merges selected values
into each application's own settings. There is no background synchronization.

| File | Purpose | Used when |
| --- | --- | --- |
| `models.json` | Shared model choices, reasoning effort and Codex service tier | CLI and T3 preference merges |
| `cli-preferences.json` | Shared Claude and Grok preferences | CLI preference merge |
| `t3/preferences.json` | Shared server, desktop, browser and model-menu preferences | T3 preference merge |
| `t3/profiles.json` | Personal/Work provider definitions and custom model options | T3 preference merge |
| `t3/keybindings.json` | Shared shortcuts with platform-specific modifiers | T3 preference merge |
| `bootstrap.json` | Seed configuration for a new proxy and fallback T3 CLI version | Installation |
| `machine.json` | This machine's role, hosts and remote-access choices, rendered from local chezmoi answers | Setup and connection commands |
| `deployment-targets.json` | Explicit file list for a targeted AI setup rollout | Deployment planning |

### Where the effective settings live

Paths below are relative to each machine's home directory.

| Application | Files it actually reads |
| --- | --- |
| Claude, including both Mixed profiles | `~/.claude/settings.json` and `~/.claude/CLAUDE.md`; Mixed launch overrides come from the proxy directory |
| Codex | `~/.codex/config.toml` |
| Grok | `~/.grok/config.toml` |
| T3 server: providers, models, title/Git-text generation and server behavior | `~/.t3/userdata/settings.json` |
| T3 desktop preferences | `~/.t3/userdata/client-settings.json` |
| T3 keyboard shortcuts | `~/.t3/userdata/keybindings.json` |
| T3 window and desktop connection settings | `~/.t3/userdata/desktop-settings.json`; window geometry stays local |
| CLIProxyAPI and its launchers | `~/.config/cli-proxy-api/`; see its [runtime guide](../cli-proxy-api/README.md) |

Edit the chezmoi source for portable changes, then deploy only the relevant input
files and helper. Preview with `claude-mixed-setup --cli-diff` or `--t3-diff`, then
use the corresponding `--apply-cli-changes` or `--apply-t3-changes`. Updating an
input file alone does not change an existing app's settings. Close T3 before
applying its preferences; start new CLI sessions to use updated defaults.
Direct changes inside an app stay local until deliberately captured in these
portable inputs. A later preference merge reapplies the selected shared keys.

The helper is `~/.local/bin/claude-mixed-setup`. The proxy directory holds live
connection settings and credentials, while private historical backups belong
under `~/.local/share/claude-archives/`, outside the public dotfiles repository.

## What chezmoi owns

The public source contains the approved `CLAUDE.md`, computer-use skill, shared
links, model routes, context budgets, agents, workflow, CLI launchers and setup
helper. `t3/preferences.json` contains the selected shared preferences; the helper
merges them into the app's local settings. Actual Claude, proxy and T3 session
files are generated locally and are never copied into the repository.

`models.json` is the shared source for model choices and effort levels.
It drives T3's conversation, title and Git-text defaults, Mixed model selectors,
and standalone Codex/Grok defaults. Astra and Sol use extra high; Fable uses
high; Opus uses extra high; Grok uses medium. Standard Codex service tier is
explicit. Session or project overrides still work. Codex's context window and
auto-compaction settings are not changed.

The catalog includes Opus 5.5, GPT-6 Sol, and GPT-6 Luna as selectable
models without changing existing defaults. Use Claude Code 2.1.280 or newer
for the Opus 5.5 Mixed route. Keep proxy protocol behavior at its upstream
defaults; no release-specific header or thinking overrides are seeded.

For a model-only rollout, preview `claude-mixed-setup --t3-diff --models-only`,
close T3, then run `claude-mixed-setup --apply-t3-changes --models-only`. This
adds missing catalog models and menu entries while retaining existing model
options, defaults, favorites, and unrelated application preferences. Deploy the
helper and the relevant inputs with a targeted chezmoi apply first.

Installations with the previous September 22 overrides can remove just those
values using `claude-mixed-setup --remove-proxy-model-workaround`; the helper
backs up the private configuration and preserves credentials and other rules.

`cli-preferences.json` contains shared Claude behaviour, attribution suppression,
the human-only `code-review` setting, and Grok display preferences. The status-line
script is shared and needs Bash, Git and jq from the OS bootstrap. Shared Bash
tool preferences use `~/.claude/hooks/prefer-modern-cli.py`; Mixed links its hooks
directory to the same location. The setup helper installs Tree-sitter Bash in an isolated
Python environment and merges the shared hook without replacing other handlers.
Use `claude-mixed-setup --apply-claude-hooks` to apply only this hook configuration.
Cargo installs `sd` in both platform bootstraps; `~/.local/bin/sd` links to the
Cargo binary so noninteractive agents can find it. Existing machine-local hooks,
plugin installations, MCP connections, notification integrations, project trust
records and credentials remain local. TOML merges preserve unrelated content and
validate the complete result before writing.

Personal and Work share `~/.claude/settings.json` through a symlink in
`~/.claude-t3-mixed/`. Edit the global file for shared preferences. The launcher
loads proxy credentials from the private `~/.config/cli-proxy-api/claude-settings.json`;
account routing and context budgets remain launch settings. First setup seeds a
missing global settings file with the workflow defaults and preserves an existing
one. On existing machines, back up the old mixed settings file and review its
preference differences before applying the symlink. `--apply-cli-changes` merges
legacy Mixed preferences into the global file, preserves its existing preferences
where they conflict, then applies the selected shared defaults and archives the old
Mixed file before linking it. Legacy proxy environment values remain in the private
connection settings. Deploy the updated launchers and preference inputs first;
perform this migration before applying the chezmoi-managed symlink.

Sonnet and Haiku retain their real model identities. Their use is prohibited by
the instructions rather than redirected to another model. The current GPT/Grok
working budget is 500K; this package does not change Codex's own context settings.

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

## First setup

The existing OS package bootstrap supplies Python, Node/npm, Tailscale and the
package manager. The AI hook installs missing CLIProxyAPI, Claude, Codex, Grok
Build and T3 components. Existing installations are preserved. T3's user-local
CLI initially matches an installed desktop version when detectable, otherwise
it uses the pin in `bootstrap.json`. Package upgrades remain explicit.

| Role | Proxy | T3 |
| --- | --- | --- |
| macOS laptop/desktop | Homebrew user service | Desktop app and CLI |
| Arch desktop/laptop | systemd user service | Desktop app and CLI |
| Arch headless | systemd user service, user lingering | CLI and persistent `t3code.service` |

The proxy listens on `127.0.0.1:8317`. Each machine generates its own gateway key.
The headless T3 service listens on loopback; Tailscale Serve supplies HTTPS for
remote clients. Desktop exposure is managed through selected T3 settings. This
package never enables public Tailscale Funnel.

For a fresh installation, the dedicated after hook runs the helper after files
and the existing package bootstrap. It includes content hashes of the helper,
defaults, profiles and preferences, plus the role/enablement choices.

For an existing machine, preview and apply only this package's targets. The
explicit target list is in `deployment-targets.json`. Exclude scripts during
that scoped apply and run the helper directly afterward; do not run a blanket
apply across unrelated dotfile drift.

```sh
claude-mixed-setup                   # read-only summary
claude-mixed-setup --install         # use the saved role and remote-access choice
claude-mixed-setup --cli-diff         # selected Claude/Codex/Grok changes only
claude-mixed-setup --apply-cli-changes
claude-mixed-setup --t3-diff          # selected T3 changes only
# Close T3; on a headless host, stop its service after active work finishes.
claude-mixed-setup --apply-t3-changes
# Reopen T3 or start its headless service when finished.
```

On first setup, missing settings files are created with shared preferences.
Existing files are left alone by `--install`; explicit preference application
makes a private backup and merges only selected keys. Model identities, existing
provider environments, credentials, other providers, project-specific state,
window geometry, and unrelated shortcuts are preserved. Existing Personal/Work
paths, launch arguments, extra custom models and private environment variables
are preserved; shared model catalog entries and routing variables are refreshed.
Shared favorites are added only when missing; locally added favorites and their
order are retained.

Browser preferences, load balancing, appearance, sidebar behaviour, confirmation
settings, Git/worktree defaults and source-control writing style are portable.
`t3/keybindings.json` keeps shared shortcuts and uses Control for thread digits
on macOS and the platform modifier on Linux. User-added shortcuts survive.
Keybindings belong to the server, including on a headless host; client appearance
preferences are applied only to desktop roles.

Close the desktop app, or finish active work and stop the headless service, before
applying T3 preferences. Desktop preferences are held in memory and can otherwise
overwrite a file edit. The helper checks for concurrent file changes and keeps
private backups. Never use a broad chezmoi apply for this migration.

Tool maintenance is a separate, explicit operation:

```sh
claude-mixed-setup --update-plan
# Finish active work and close T3 / stop its headless service first.
claude-mixed-setup --update-tools
```

The updater uses the existing installation owner: Codex/Grok's native updater
for standalone installations, Homebrew for its installations, and yay/paru for
Arch packages. Arch updates include a full system upgrade to avoid unsupported
partial upgrades. The T3 CLI follows the installed desktop version; headless
maintenance uses the current npm release and updates the installed service.
No package upgrades run automatically during chezmoi apply.

Installation is repeatable: existing gateway keys and subscriptions survive;
running services are not restarted and existing packages are not upgraded.
A conflicting service or Tailscale Serve mapping requires review. Existing T3
settings cannot be modified while its backend is running.

T3's service installer creates a separate npm runtime. Native script approval is
limited to `node-pty` and `msgpackr-extract` in a temporary npm configuration for
that installation, with the user's other npm settings retained. No global npm
policy is changed. Arch setup may require local sudo authentication and lingering
permission. Missing Tailscale login is reported for completion on that machine.

## Subscription login

Run these on the host where the agents execute:

```sh
cpapi login personal
cpapi login work
cpapi login openai
cpapi login grok
cpapi status
```

Personal and Work use separate Claude subscriptions and share that machine's
connected OpenAI/Grok subscriptions. The helper prevents pinning the same Claude
account/workspace to both names. Login enables the corresponding mixed profile.
For browser callbacks over SSH, use the provider's login options and the indicated
callback port forwarding; never paste tokens into the repository.

The native Codex and Grok providers in T3 use their own CLI login stores. Complete
those logins locally too if using them for default tasks, titles or Git text.
CLIProxyAPI login does not automatically sign those separate clients in.

Ordinary terminal use is available through `claude-personal` and `claude-work`.
For an on-demand workflow snapshot, run `~/.claude/scripts/claude-workflow-status <session-directory> <workflow-id>`;
the session directory contains `subagents/` and `workflows/`. Add `--json` for
metadata suitable for filtering. The command reads nested agent activity, never
stops agents, and treats seven minutes of inactivity as a reason to inspect rather
than proof of a stall. It needs only Python's standard library.
The computer-use skill requires an installed Codex tool environment; copying it
does not install browser/desktop tools or establish GUI automation on Linux.

## Remote environments and phone access

```sh
claude-mixed-setup --connections
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
