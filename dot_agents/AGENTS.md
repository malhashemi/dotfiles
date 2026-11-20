## Models for delegated work

Every session runs inside T3 Code, which can start a child task on any harness and model. Use the main thread, subagents, delegated tasks, or workflows as the task warrants; each delegated seat goes to the model that owns that role below.

### Roles

- **Opus 5.5** is the main worker for delegated work: implementation, UI, backend, and final synthesis. It owns the result. Run it at `high`, including for ordinary UI work; use `xhigh` only when prototyping a new UI from scratch.
- **Gemini 4 Neon** is the primary copywriter for all user-facing writing (UI copy, labels, empty/error states, product/marketing copy, Dossier pages, and docs): draft copy up front for Opus 5.5 to use verbatim, or run a copy pass over rendered strings and prose. It is also the fallback implementer when Opus 5.5 is unavailable (quota exhausted or API unreachable; fall back to Sol 6.2 at `high` only if both are unavailable). Don't use it for implementation when Opus is available.
- **Sol 6.1** is the default codebase researcher: deep codebase investigation, and locating and understanding code and tasks.
- **Sol 6.2** is the primary independent reviewer when review is warranted (substantial or risky change, or user-requested), and handles browser and web runtime verification (driving a running web app, browser, simulator, or device and capturing screenshots or recordings when real interaction is needed; not for what the main thread can check itself).
- **Astra 6.2** is the reviewer for high-stakes, security-sensitive, or subtle cross-cutting audits (use `xhigh` for the hardest audits), and handles native desktop/OS GUI computer use outside a browser DOM (native dialogs, desktop apps, `computer-use-linux`).
- **Fable 5.2** may be delegated only for greenfield visual direction / UI architecture (when no design system exists) or as an advisor when Opus 5.5 stalls on a hard architectural problem. Never delegate routine implementation, lookups, or reviews to it; if the main thread runs on Fable 5.2, still pin delegated seats to their role models above.
- **Grok 4.7** is optional and narrow: simple file location and straightforward lookups, or a supplementary adversarial review alongside Codex. It is never the primary reviewer or an implementer. Don't invent a task just to use it.
- Research, review, and computer-use seats report findings and do not edit files unless the brief allows it.
- The user chooses the model for design work. Don't route design work to a different model automatically; unless the user picks one, design work follows the roles above.
- Never use Sonnet or Haiku, at any effort, including wrappers and background workers.
- The Sonnet and Haiku ban covers simple tasks too. Delegate a simple file-location or straightforward lookup task only to Grok 4.7; otherwise do it in the main thread.

### When to delegate

Delegation pays for itself in three ways; use it when one applies:

- **Time:** independent work runs concurrently instead of in sequence.
- **Context:** a long task keeps its judgement when the main thread delegates the building and keeps its own context for integration and decisions.
- **Independence:** a reviewer or test author who did not build the code checks what was required rather than what was built.

Small, tightly coupled work is usually faster in the main thread. Always orchestrate when the user explicitly asks for it. Orchestration decides how work is split, not who does it: however many agents are involved, implementation seats go to Opus 5.5 (or Gemini 4 Neon / Sol 6.2 only under the fallback), user-facing copy goes to Gemini 4 Neon, and the other models keep their roles.

### Reaching each model

Use your harness's native subagent tool when it can run the role's model at the role's effort. Otherwise delegate through T3's `delegate_task`, whose own instructions cover review rounds, retries, and isolation.

| Role | T3 provider instance | Model | Option |
|---|---|---|---|
| Opus 5.5 | `claudeAgent`, unless the project's instructions name another | `claude-opus-5-5` | `effort: high` |
| Fable 5.2 | `claudeAgent` | `claude-fable-5-2` | `effort: high` |
| Gemini 4 Neon | `antigravity` | `gemini-4-neon` | `thinking_level: high` |
| Sol 6.1 | `codex` | `gpt-6.1-sol` | `reasoningEffort: xhigh` |
| Sol 6.2 | `codex` | `gpt-6.2-sol` | `reasoningEffort: xhigh` |
| Astra 6.2 | `codex` | `gpt-6.2-astra` | `reasoningEffort: high` |
| Grok 4.7 | `grok` | `grok-4.7` | `reasoningEffort: xhigh` |

- Set the provider, model, and effort explicitly on every seat, so none runs on a default (Codex defaults to `low`; `claude-opus-5-5` also appears under `antigravity`). Keep delegated Codex seats on Standard tier.
- Give each seat a self-contained brief: the task, its role, its constraints, and whether it may edit files. Seats don't see this conversation.
- Parallel editing seats work in separate files or isolated worktrees, so their changes don't collide.
- When a role's model can't be reached, give its work to an Opus seat or the main thread and tell the user; an Opus review does not cross providers.

### Computer use

Brief a computer-use seat with what to verify and on which platform, how to launch the app, any credentials, seed data, or fixtures it needs, and where to save screenshots and logs. Ask for pass, fail, or blocked, with the steps taken, what was observed, and the screenshot paths.

Launching apps, simulators, or browsers to verify work is fine without asking. Ask the user first only when a run could disrupt their environment beyond that, such as closing their apps, changing system settings, or acting on real accounts or data.

### Browsers

Pick the browser by the job, and don't try several.

- **The app you're building** (localhost or the project's preview): T3's preview browser (the `preview_*` tools).
- **Sites that need the user's sign-ins** (dashboards, consoles, admin pages): Codex uses its own browser use, through Chrome and the ChatGPT extension. Other harnesses, and Codex where that isn't available, use agent-browser. On an agent desktop, attach it to the signed-in agent Chrome with `agent-browser --cdp 9222`.
- **Anything outside a web page** (extension popups, native dialogs, desktop apps): computer use. On Linux that's the `computer-use-linux` MCP server.
- Don't use Claude in Chrome, Claude desktop's built-in browser, or terminal-browser.

Before signing in to a service, check the fleet runbook for which account it uses; some are split between a work and a personal account. When a sign-in needs a code, passkey, or phone approval, stop and ask the user, saying which service, which account, and any number to match. Don't retry a failed verification: repeated failures lock the account.

## Shell tools

<important if="you are running shell commands">
- Use rg to search file contents.
- Use fd to locate files.
- Use sd for search and replace.
- Use jq to extract JSON values.
- Use xh for HTTP requests.
</important>
