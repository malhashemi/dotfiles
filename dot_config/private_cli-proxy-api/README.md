# Local CLIProxyAPI

One local proxy serves a mutable provider-neutral account pool. See
`~/.config/ai-setup/README.md` for rollout and account commands.

`accounts.json`, `auth/`, `client-key`, `management-key`, and `config.yaml` are
private generated machine state. Never commit their contents or copy OAuth
sign-ins across machines. Management stays on localhost:8317.

`plugins/` holds the quota-reset-router library, placed by
`~/.local/bin/install-quota-router`. chezmoi ignores this directory. The proxy
loads a library only at startup, so upgrade by stopping the proxy, rerunning
the installer, then starting it again. Claude accounts share priority 100, so
the plugin can choose by soonest weekly reset.

`cpapi --help` lists account and service commands. Account login is staged and
never creates T3 providers. Optional `claude-openai`, `claude-grok`, and
`claude-multi` launchers remain available; ordinary Claude uses the native
shared settings and pooled Claude routes.
