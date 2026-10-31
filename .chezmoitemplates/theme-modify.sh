{{- /*
  Shared body of the theme-system modify_ scripts. Each caller passes:
    app   theme-system app name (see APPS in theme-modify.py)
    base  the repo's version of the file (.theme-bases/), already rendered
    ctx   the template data (.)

  The output is the base with the app's theme-system module applied using
  this machine's theme data, so chezmoi manages the settings and the colors
  stay whatever the theme-system last set. The helper and the modules are run
  from the source dir, because ~/.config/theme-system may not exist yet.
*/ -}}
{{- $src := .ctx.chezmoi.sourceDir -}}
#!/bin/sh
# chezmoi modify_ script (theme-system app: {{ .app }}).
# Generated from .chezmoitemplates/theme-modify.sh; edit the base in .theme-bases/.
set -eu
tmp=$(mktemp -d "${TMPDIR:-/tmp}/theme-modify.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
printf '%s' '{{ .base | b64enc }}' | base64 --decode >"$tmp/base"
{{- if and (hasKey .ctx "theme") .ctx.theme }}
cat >"$tmp/current"
PATH="$PATH:$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin"
if command -v uv >/dev/null 2>&1; then
  PYTHONUTF8=1 uv run --quiet --script \
    "{{ joinPath $src "dot_config/theme-system/scripts/executable_theme-modify.py" }}" \
    {{ .app }} --base "$tmp/base" \
    --theme-data "{{ joinPath $src ".chezmoidata/theme.yaml" }}" <"$tmp/current"
else
  echo "theme-modify ({{ .app }}): uv not found; leaving the file as it is" >&2
  if [ -s "$tmp/current" ]; then cat "$tmp/current"; else cat "$tmp/base"; fi
fi
{{- else }}
# No theme data on this machine yet: the file is the base.
cat >/dev/null
cat "$tmp/base"
{{- end }}
