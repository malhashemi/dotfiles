## Models for delegated work

Every session runs inside T3 Code, which can start a child task on any harness and model. Use the main thread, subagents, delegated tasks, or workflows as the task warrants; each delegated seat goes to the model that owns that role below.

### Roles

- **Opus 5.5** (`claude-opus-5-5`) is the main worker for delegated work: implementation, UI, backend, writing, and final synthesis. It owns the result. Run it at effort `high`, including for ordinary UI work; use `xhigh` only when prototyping a new UI from scratch.
- **Fallback:** if Opus 5.5 is actually unavailable (for example, its quota is exhausted or its API is unreachable), Sol 6.1 at `high` may serve as the implementer and main worker. Don't choose Sol 6.1 for this when Opus is available.
- **Sol 6.1** (`gpt-6.1-sol`, always `xhigh` for review, research, and computer use) is the primary independent reviewer when review is warranted: the change is substantial or risky, or the user asks for review. It is also the researcher: deep codebase investigation, and locating and understanding code and tasks. It also handles computer use: driving a running app, browser, simulator, or device, and capturing screenshots or recordings, when a check needs real interaction or an independent look at runtime behaviour; don't use it for what the main thread can check itself, such as reading code or running tests. In these roles it reports findings and does not edit files unless the brief allows it.
- **Grok 4.7** (`grok-4.7`, effort `xhigh`) is optional and narrow: simple file location and straightforward lookups, or a supplementary adversarial review alongside Sol 6.1. It is never the primary reviewer or an implementer. Don't invent a task just to use it.
- The user chooses the model for design work. Don't route design work to a different model automatically; unless the user picks one, design work follows the roles above.
- Never use Fable, at any effort.
- Never use Sonnet or Haiku, at any effort, including wrappers and background workers.
- The Sonnet and Haiku ban covers simple tasks too. Delegate a simple file-location or straightforward lookup task only to Grok 4.7; otherwise do it in the main thread.

### When to delegate

Delegation pays for itself in three ways; use it when one applies:

- **Time:** independent work runs concurrently instead of in sequence.
- **Context:** a long task keeps its judgement when the main thread delegates the building and keeps its own context for integration and decisions.
- **Independence:** a reviewer or test author who did not build the code checks what was required rather than what was built.

Small, tightly coupled work is usually faster in the main thread. Always orchestrate when the user explicitly asks for it. Orchestration decides how work is split, not who does it: however many agents are involved, implementation seats go to Opus 5.5 (or Sol 6.1 only under the fallback), and the other models keep their roles.

### Reaching each model

Use your harness's native subagent tool when it can run the role's model at the role's effort. Otherwise delegate through T3's `delegate_task`, whose own instructions cover review rounds, retries, and isolation.

| Role | T3 provider instance | Model | Option |
|---|---|---|---|
| Opus 5.5 | `claude-mixed-a`, unless the project's instructions name another | `claude-opus-5-5` | `effort: high` |
| Sol 6.1 | `codex` | `gpt-6.1-sol` | `reasoningEffort: xhigh` |
| Grok 4.7 | `grok` | `grok-4.7` | `reasoningEffort: xhigh` |

- Set the model and effort explicitly on every seat, so none runs on a default.
- Give each seat a self-contained brief: the task, its role, its constraints, and whether it may edit files. Seats don't see this conversation.
- Parallel editing seats work in separate files or isolated worktrees, so their changes don't collide.
- When a role's model can't be reached, give its work to an Opus seat or the main thread and tell the user; an Opus review does not cross providers.

### Computer use

Brief a computer-use seat with what to verify and on which platform, how to launch the app, any credentials, seed data, or fixtures it needs, and where to save screenshots and logs. Ask for pass, fail, or blocked, with the steps taken, what was observed, and the screenshot paths.

Launching apps, simulators, or browsers to verify work is fine without asking. Ask the user first only when a run could disrupt their environment beyond that, such as closing their apps, changing system settings, or acting on real accounts or data.

## Shell tools

<important if="you are running shell commands">
- Use rg to search file contents.
- Use fd to locate files.
- Use sd for search and replace.
- Use jq to extract JSON values.
- Use xh for HTTP requests.
</important>
