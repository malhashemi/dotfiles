@~/.agents/AGENTS.md

## Claude Code

- Native Opus seats: `subagent_type: "opus"` with `effort` set per role. Don't pass `model`; it replaces the pinned model.
- Workflows run Claude workers only. Use them to coordinate several Opus seats, passing `{model: "claude-opus-5-5", effort: "high"}` to each worker; reach Sol and Grok from the main thread through T3.
- Check a workflow's progress with `~/.claude/scripts/claude-workflow-status <session-directory> <workflow-id>`, passing the session directory that contains `subagents/`. A quiet parent or a `needs inspection` status alone is not a reason to stop a workflow.
- If a built-in, plugin, or helper agent would run on Sonnet or Haiku, set its model explicitly or don't use it.
