<thoughts-cli-awareness>

<overview>
Most projects in this ecosystem are thoughts-mapped: documentation and work artifacts live under a `thoughts/` directory governed by the `thoughts` CLI. The CLI exposes a small set of operations you can rely on, and ecosystem-wide conventions govern how artifacts are shaped.
</overview>

<commands>
  <command name="thoughts metadata">Returns the session's owner, ISO 8601 date, repository, branch, commit, team, and `shared_folder` (the absolute path where bundle artifacts live). Call this when you need session context.</command>
  <command name="thoughts validate &lt;file...&gt;">Checks frontmatter against the team's schema. A non-zero exit code means malformed frontmatter.</command>
  <command name="thoughts backlog next">Surfaces the next backlog item via PageRank over the `depends_on` graph. Use when picking up work.</command>
  <command name="thoughts backlog blocked">Lists items blocked by unfinished dependencies.</command>
</commands>

<bundle-convention>
Artifacts produced by workflow agents live at `{shared_folder}/<category>/<slug>/` (e.g., `<shared>/tickets/team-workspaces/`) with schema-valid YAML frontmatter:

- Both `owner:` and `researcher:` are populated from `thoughts metadata`.
- `last_updated:` is a full ISO 8601 datetime (not a date-only value).
- Wiki-links — in `parent:`/`children:` and anywhere in an artifact's body —
  target a **filename stem**: write `[[file-stem]]`, or `[[file-stem|display text]]`
  to show other text. The token before the `|` must be a real file's stem; a
  `[[alias]]` that is not itself a filename is a dangling link.
- Custom frontmatter fields are forbidden unless the team config explicitly permits them.
</bundle-convention>

<rules>
  <rule>If the repository is not thoughts-mapped, `thoughts metadata` returns a reduced default schema (no `shared_folder`, no `team`). Workflow agents that depend on bundles should detect this and halt with a clear message — they cannot operate without a thoughts context.</rule>
  <rule>Workflow scripts call `thoughts metadata` internally. When invoking a workflow script (e.g., a scaffold script), pass only domain arguments. The script fetches its own session metadata to guarantee freshness.</rule>
</rules>

</thoughts-cli-awareness>
