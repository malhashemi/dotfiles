# Research Dispatch

This reference is loaded during the Q↔R loop. All research dispatch goes through the `researcher` agent — ticket-grill does not dispatch the research children directly. researcher selects the children, dispatches them in parallel, and synthesizes the findings; ticket-grill composes the questions and consumes the synthesis.

## One researcher dispatch per turn

A Q↔R turn that triggers research composes its research-agenda questions and dispatches `researcher` ONCE with the batch. researcher runs its Quick Answer capability: it infers the right child per question shape, dispatches the children in parallel, validates and sharpens vague returns, and returns per-question synthesized findings. Parallelism is researcher's concern, not ticket-grill's.

## Composing a research question

Each research-agenda question carries:

- **question_text** — WHAT to find, stated specifically (names the file/concern/keyword)
- **scope** — WHERE to look (directory globs, file paths, or domain)
- **expected_output_shape** — e.g., "markdown table with file:line and one-line purpose"
- **child_subagent_hint** (optional) — when the shape clearly maps to one child, name it; researcher honors the hint and infers the child itself when it is omitted

The question carries ONLY the above — never the ticket, the parent decision context, or the design intent. researcher is blind to the change's intent by design, and gathers facts, not opinions about what to change.

A vague question returns generic findings; a specific one returns crisp facts. Spend the time to shape it well.

| Question shape | Typical child hint |
|---|---|
| "Does X exist in the codebase?" | codebase-locator |
| "How does X work today?" | codebase-analyzer |
| "Is there a pattern for X?" | codebase-pattern-finder |
| "Have we discussed X before?" | thoughts-locator (then thoughts-analyzer) |
| "What do other systems do for X?" | web-search-researcher (needs approval) |

## Cap discipline

Cap research-agenda questions at 4 per turn. Beyond that, the turn's focus is too wide to synthesize into the research file without losing fidelity — split into two turns.

## Web search approval gate

Any research-agenda question that needs external/web research requires user approval before dispatch, per QRDSPIV §3.1 mode-shift rules. Ask via the Question tool; if approved, pass `web_search_approved: true` to researcher. If declined, drop the web question and note the deferral in the questions file.

## Direct reads are not research dispatch

Some questions are answered by reading a known file directly (bundle files, CONTEXT.md, a DR at a known path, briefs in thoughts/). Those are artifact checks — read them directly, no researcher dispatch needed.
