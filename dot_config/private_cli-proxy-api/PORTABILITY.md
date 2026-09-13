# Shared AI setup: macOS and Arch Linux

## What chezmoi owns

The public source contains the approved `CLAUDE.md`, computer-use skill, shared
links, model routes, context budgets, agents, workflow, CLI launchers and setup
helper. `t3-preferences.json` contains the selected shared preferences; the helper
merges them into the app's local settings. Actual Claude, proxy and T3 session
files are generated locally and are never copied into the repository.

Personal and Work share `~/.claude/settings.json` through a symlink in
`~/.claude-t3-mixed/`. Edit the global file for shared preferences. The launcher
loads proxy credentials from the private `~/.config/cli-proxy-api/claude-settings.json`;
account routing and context budgets remain launch settings. First setup seeds a
missing global settings file with the workflow defaults and preserves an existing
one. On existing machines, back up the old mixed settings file and review its
preference differences before applying the symlink; retain wanted preferences in
the global file. Apply the updated launchers together with the symlink.

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
`~/.config/cli-proxy-api/machine.json` passes only required machine configuration
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
it uses the pin in `defaults.json`. Package upgrades remain explicit.

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
claude-mixed-setup --t3-diff          # selected changes only
# Close T3; on a headless host, stop its service after active work finishes.
claude-mixed-setup --apply-t3-changes
# Reopen T3 or start its headless service when finished.
```

On first setup, missing settings files are created with shared preferences.
Existing files are left alone by `--install`; explicit preference application
makes a private backup and merges only selected keys. Model identities, existing
provider environments, credentials, other providers, project-specific state,
window geometry, and platform-specific shortcuts are preserved. Existing
Personal/Work provider configuration is not replaced.
Shared favorites are added only when missing; locally added favorites and their
order are retained.

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
