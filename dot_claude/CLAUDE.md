## Models for delegated work

The main thread generally does most substantive work. Use subagents or workflows whenever they help; whichever you choose, each seat goes to the model that owns that role below.

### Roles

- **Opus 5.5** (`claude-opus-5-5`, effort `high`) is the main worker for delegated work: implementation, UI, backend, writing, and final synthesis. It owns the result.
- **Fallback:** if Opus 5.5 is actually unavailable (for example, its quota is exhausted or its API is unreachable), Astra at `xhigh` may serve as the implementer and main worker. Don't choose Astra for this when Opus is available.
- **Astra** (`gpt-6-astra`, always `xhigh`) is the primary independent reviewer when review is warranted: the change is substantial or risky, or the user asks for review.
- **Sol 6** (`gpt-6-sol`, always `xhigh`) is strictly a researcher: deep codebase investigation, and locating and understanding code and tasks. It reports findings; it does not implement or edit files.
- **Grok 4.7** is optional and narrow: simple file location and straightforward lookups, or a supplementary adversarial review alongside Astra. It is never the primary reviewer or an implementer. Don't invent a task just to use it. Use the model ID and highest effort that the current harness lists for Grok 4.7; don't guess either.
- The user chooses the model for design work. Don't route design work to a different model automatically; unless the user picks one, design work follows the roles above.
- Never use Fable, at any effort.
- Never use Sonnet or Haiku, at any effort, including wrappers and background workers.
- The Sonnet and Haiku ban covers simple tasks too. Delegate a simple file-location or straightforward lookup task only to Grok 4.7; otherwise do it in the main thread. If a built-in, plugin, or helper agent would run on Sonnet or Haiku, set its model explicitly or don't use it.

### Subagents and workflows

- Use your judgment about when subagents or workflows help, for example exploratory work, parallel investigation, multi-step coordination, or a review-and-fix loop.
- A plain subagent suits a single well-scoped seat: a Sol investigation, an Astra review, or an Opus implementation that benefits from isolated context.
- A workflow suits work with several steps or seats to coordinate, such as sequenced phases, shared artifacts, or comparing approaches.
- Always orchestrate when the user explicitly asks for it.
- Orchestration decides how work is split, not who does it. However many agents are involved, implementation seats go to Opus 5.5 (or to Astra only under the fallback above), and the other models keep their roles above.
- When checking workflow progress, run `~/.claude/scripts/claude-workflow-status <session-directory> <workflow-id>` through Bash. Pass the session directory containing `subagents/`; the report includes nested agents. A quiet parent or a `needs inspection` status alone is not a reason to stop a workflow.

### Mechanics

- Reach every model directly through the native Agent/Workflow `model` parameter, using the IDs above. Do not launch `codex exec`, `codex review`, or another provider CLI to reach them. The exception is a skill that requires a CLI for a capability the native tools lack, such as `codex-computer-use` running Astra through `codex exec` for computer-use verification.
- Set `effort` explicitly on every worker with the actual `effort` parameter, using the effort given for its role above, so it doesn't inherit the coordinator's effort.
- In Workflow, pass both in the worker options, for example `agent(task, {model: "claude-opus-5-5", effort: "high"})`.
- Parallel editing agents must use separate files or `isolation: "worktree"` so their changes do not collide.

## Notes

<important if="you are using Bash">
- Use rg to search file contents.
- Use fd to locate files.
- Use sd for search and replace.
- Use jq to extract JSON values.
- Use xh for HTTP requests.
</important>
