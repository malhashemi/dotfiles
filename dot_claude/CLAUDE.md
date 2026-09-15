## Picking the right models for workflows and subagents

Rankings are relative, where higher = better.

Cost efficiency reflects subscription limits, not API list prices. OpenAI has generous limits, so gpt-5.6-sol is effectively cheap for my usage. Intelligence means how hard a problem the model can handle unsupervised. Design taste covers UI/UX, code quality, and API design. Writing taste covers copy and prose. Speed means time to a correct result.

| Model | Effort | Intelligence | Design Taste | Writing Taste | Speed | Cost Efficiency |
|---|---|---:|---:|---:|---:|---:|
| gpt-6-astra | high | 9.6 | 5.5 | 8.0 | 8.2 | 7.5 |
| gpt-6-astra | xhigh | 9.8 | 5.5 | 8.0 | 7.2 | 7.1 |
| gpt-6-astra | max | 9.8 | 5.5 | 8.0 | 6.1 | 5.3 |
| claude-fable-5-1 | high | 9.5 | 9.8 | 9.5 | 5.5 | 4.0 |
| claude-fable-5-1 | xhigh | 9.6 | 9.7 | 9.5 | 4.5 | 3.0 |
| claude-fable-5-1 | max | 9.7 | 9.6 | 9.5 | 3.0 | 2.0 |
| gpt-5.6-sol | high | 8.8 | 5.0 | 8.5 | 8.4 | 9.5 |
| gpt-5.6-sol | xhigh | 9.1 | 5.0 | 8.5 | 7.3 | 8.6 |
| gpt-5.6-sol | max | 9.3 | 5.0 | 8.5 | 5.9 | 7.0 |
| claude-opus-5 | high | 8.3 | 8.9 | 4.0 | 5.7 | 6.5 |
| claude-opus-5 | xhigh | 8.6 | 8.9 | 4.0 | 4.9 | 5.3 |
| claude-opus-5 | max | 8.8 | 8.8 | 4.0 | 4.5 | 4.6 |
| grok-4.6 | medium | 8.2 | 7.0 | 6.5 | 5.7 | 7.7 |
| grok-4.6 | high | 8.0 | 7.0 | 6.5 | 5.2 | 7.0 |
| grok-4.6 | xhigh | 8.2 | 7.0 | 6.5 | 4.9 | 6.3 |

### My model and effort preferences

Use these as defaults, not restrictions. Choose differently when the task warrants it, without asking.

- For orchestration, prefer Astra at xhigh or Fable at high.
- Prefer Fable at high for visual design from scratch, API design, and decisions where design judgment matters most.
- Prefer Astra at xhigh for difficult reasoning, deep investigation, deep review, and exploratory discussion.
- Prefer Sol at xhigh for deep codebase analysis and implementation against established APIs or designs. Generally prefer it over Opus outside visual work.
- Prefer Opus at xhigh or max for visual implementation with some design freedom. Prefer Sol over Opus for writing.
- Prefer Grok at medium for locating files, straightforward lookups, and optional supplementary review.

### How to apply

- You have standing permission to escalate: if a cheaper model's output does not meet the bar, rerun or redo the work with a smarter model without asking.
- Judge the output, not the price tag. Escalating costs less than shipping mediocre work.
- Cost efficiency is a tie-breaker only. When axes conflict for anything that ships, prioritise intelligence, then the relevant taste dimension, then speed, then cost efficiency.
- For bulk or mechanical work, consider gpt-5.6-sol's cost efficiency. Choose the model and effort that meet the actual task's quality bar.
- Anything user-facing needs taste >= 7 in the relevant dimension. Examples: UI, copy, API design, product-facing naming, and developer experience.
- Primary independent reviews must cross Anthropic and OpenAI: use Astra or Sol to review Fable or Opus work, and Fable or Opus to review Astra or Sol work.
- Grok may provide an optional additional or adversarial review; it must not serve as the primary independent reviewer.
- Never use Sonnet or Haiku, at any effort, including wrappers and background workers.

### Workflows vs subagents

- Prefer workflows when the work has sequencing, multiple reviewers or implementers, shared artifacts, structured outputs, budget tracking, or a clear review/merge loop.
- Prefer workflows when comparing models or approaches. They make routing, labels, intermediate results, and final synthesis easier to inspect.
- Use a plain subagent for a single independent task: isolated investigation, narrow review, or quick implementation where orchestration would add ceremony.
- If a task starts as a subagent but grows coordination needs, switch to a workflow rather than continuing with ad hoc delegation.
- When checking workflow progress, run `~/.claude/scripts/claude-workflow-status <session-directory> <workflow-id>` through Bash. Pass the session directory containing `subagents/`; the report includes nested agents. A quiet parent or a `needs inspection` status alone is not a reason to stop a workflow.

### Mechanics

- Every model in the table is reachable directly through the native Agent/Workflow `model` parameter. Use the model IDs in the table; do not launch `codex exec`, `codex review`, or another provider CLI to reach them.
- Choose effort independently for each worker with the actual `effort` parameter: `low`, `medium`, `high`, `xhigh`, or `max`. Grok supports only the first four; set an explicit supported effort when the coordinator is at `max`. Low and medium remain available for all models.
- In Workflow, pass both in the worker options, for example `agent(task, {model: "gpt-6-astra", effort: "high"})`.
- Parallel editing agents must use separate files or `isolation: "worktree"` so their changes do not collide.

## Notes

<important if="you are using Bash">
- Use rg to search file contents.
- Use fd to locate files.
- Use sd for search and replace.
- Use jq to extract JSON values.
- Use xh for HTTP requests.
</important>

<important if="you are using the rpi:create-structure-outline skill">
- Every exported symbol gets a full signature; declare each shared type once and reference it by name; add a per-phase "how it connects" note.
- The skill's "concise" instruction is scoped to prose, not signatures.
</important>

<important if="you are using the rpi:implement-outline skill">
- When workflow orchestration is available, it supersedes the skill's one-phase-at-a-time Agent loop and mandatory human confirmation between phases. Use a workflow to implement and independently verify each phase in order, continuing through the requested phase scope without pausing.
- Route implementation, review, and verification seats across the available model fleet according to each phase's needs and each model's strengths; do not default every seat to the skill's fixed implementer-agent pattern.
- Treat `Manual Verification` items as verification requirements, not automatic human gates: assign them to capable agents or tools when possible, and stop only when a check genuinely requires human judgment or a material blocker or decision is reached.
</important>
