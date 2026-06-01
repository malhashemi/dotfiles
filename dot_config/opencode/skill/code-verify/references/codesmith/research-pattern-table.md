<research-pattern-table>

<overview>
Seven composable patterns. A turn may use one alone or combine 2-4 in parallel via `researcher`. Cap: 4 subagents per turn.
</overview>

<patterns>

<pattern name="codebase-navigate">
| Aspect | Detail |
|---|---|
| When applied | What / How / Where questions about the codebase as it currently exists |
| Output | File paths + line refs + patterns observed |
| Child subagents | `codebase-locator` (find files matching purpose), `codebase-analyzer` (deep-dive specifics), `codebase-pattern-finder` (find similar implementations) |
| Composes with | All others |
| Example | "How does authentication wire into the request pipeline?" → `codebase-analyzer` with scope `src/middleware/`, `src/routes/` |
</pattern>

<pattern name="thoughts-navigate">
| Aspect | Detail |
|---|---|
| When applied | Why questions on historical decisions; ticket bundle references prior DRs/ADRs |
| Output | Findings from prior thoughts/ artifacts (research docs, briefs, DRs) |
| Child subagents | `thoughts-locator` (broad — find candidate artifacts), `thoughts-analyzer` (deep — read specific artifacts). Dispatch in parallel; locator's findings feed analyzer's next-turn scope. |
| Composes with | All others, especially codebase-navigate |
| Example | "Why did the team choose synchronous HTTP between Ordering and Billing in 2025?" → `thoughts-locator` for prior ADRs + `thoughts-analyzer` on the candidates it surfaces |
</pattern>

<pattern name="architecture-zoom">
| Aspect | Detail |
|---|---|
| When applied | Mental model of the touched area is shallow; needs a higher-level map before deeper investigation can target effectively |
| Output | Module map in project vocabulary (per CONTEXT.md) with callers, dependents, and architectural seam locations |
| Child subagents | `codebase-analyzer` with broad scope and the prompt: "go up a layer of abstraction; give me a map of all the relevant modules and callers, using the project's domain glossary vocabulary" |
| Composes with | Precedes others — establishes the map first, then deeper patterns target specific areas |
| Example | "I don't know how the payment subsystem fits into the rest of the order flow." → `codebase-analyzer` with zoom-out framing |
</pattern>

<pattern name="prototype">
| Aspect | Detail |
|---|---|
| When applied | Questions answerable only by running code (state-machine feel, data-model trade-off, performance characteristic). NOT for documentation or pattern questions. |
| Output | Throwaway runnable artifact + findings absorbed back into the research synthesis (no separate findings document) |
| Child subagents | None directly — invoke the `ticket-prototype` standalone skill. LOGIC branch for terminal/state questions; UI branch for visual/flow questions. |
| Composes with | After codebase-navigate has mapped the territory |
| Example | "Will the new aggregation API's pagination model feel right for the typical query?" → invoke `ticket-prototype` LOGIC branch |
</pattern>

<pattern name="diagnose-feedback-loop">
| Aspect | Detail |
|---|---|
| When applied | Ticket tag is `bug`; turn dominated by Why questions about a specific failure mode |
| Output | Reproduction harness + isolated failure signal + ranked hypotheses (3-5, falsifiable, with predictions) |
| Child subagents | `codebase-analyzer` to map the bug's code path; possibly `codebase-pattern-finder` for similar past bugs |
| Composes with | Often the SOLE pattern in the first turn of a bug ticket; later turns add codebase-navigate to verify the fix's seam |
| Example | "Aggregation returns wrong count when items have null timestamps." → `codebase-analyzer` for the aggregation pipeline + reproduction harness scaffold |

Diagnose discipline (6 phases):

1. Build a feedback loop. Be aggressive, be creative, refuse to give up.
2. Reproduce — confirm the loop produces the user-described failure.
3. Hypothesise — 3-5 ranked falsifiable hypotheses BEFORE testing any.
4. Instrument — one variable at a time; tag every debug log with `[DEBUG-NNNN]`.
5. Fix + regression test — test before fix, only at a correct seam.
6. Cleanup + post-mortem — original repro gone, regression test passes, debug logs removed, hypothesis captured in commit/PR.
</pattern>

<pattern name="external-research">
| Aspect | Detail |
|---|---|
| When applied | Why questions about industry patterns or library capabilities not in the codebase; cross-system comparison |
| Output | External findings (docs, blog posts, vendor comparisons, competitor patterns) absorbed into the research synthesis |
| Child subagents | `web-search-researcher`. Requires user approval before dispatch. Suggested phrasing: "This question would benefit from external research — how other systems (e.g., {{named-competitor-or-tool}}) handle this. May I dispatch a web search?" |
| Composes with | Supplement to codebase-navigate; rare; never the primary pattern |
| Example | "How do Stripe and Adyen handle webhook idempotency at scale?" → `web-search-researcher` with user approval |
</pattern>

<pattern name="escape-hatch">
| Aspect | Detail |
|---|---|
| When applied | The question doesn't fit any of the six patterns above |
| Output | Surface to user via Question tool: propose a new pattern OR abort the turn |
| Child subagents | None — recognition mechanism, not dispatch action |
| Composes with | Replaces other patterns when invoked |
| Example | "Should we ask the user community what they want here?" — not research; product decision; route to user |
</pattern>

</patterns>

<dispatch-discipline>
Choose the smallest set of patterns covering the active question shapes. Do not dispatch four subagents to look impressive — context, wall-clock, and subagent quality all degrade with vague prompts.

Cap: 4 subagents per turn. Beyond that, the turn becomes unsynthesizable. If a turn genuinely needs more, narrow the focus.

Subagent prompt anatomy — every prompt names:

1. WHAT to find (the question)
2. WHERE to look (directory, concern, keyword)
3. CONSTRAINTS (e.g., "do not analyze; just locate", "limit to TypeScript files")
4. OUTPUT SHAPE (e.g., "markdown table with file:line and one-line purpose")

Synthesize, never paste. Subagent output is discarded after synthesis; citations (file:line, URL, prior thought alias) go inline in the synthesis.

Wait for all dispatched subagents before synthesizing. Partial synthesis is worse than full synthesis a few minutes later.
</dispatch-discipline>

<question-shape-quick-reference>
| Question shape | Pattern | Child subagent(s) |
|---|---|---|
| "Does X exist?" | codebase-navigate | `codebase-locator` |
| "How does X work today?" | codebase-navigate | `codebase-analyzer` |
| "Is there a pattern for X?" | codebase-navigate | `codebase-pattern-finder` |
| "Why did we choose X over Y?" | thoughts-navigate | `thoughts-locator` + `thoughts-analyzer` |
| "What's the shape of subsystem Z?" | architecture-zoom | `codebase-analyzer` (zoomed-out) |
| "Will this data model feel right?" | prototype | invoke `ticket-prototype` (LOGIC) |
| "Does this UI flow work?" | prototype | invoke `ticket-prototype` (UI) |
| "Why does this bug occur?" | diagnose-feedback-loop | `codebase-analyzer` + reproduction harness |
| "What do other systems do?" | external-research | `web-search-researcher` (user-approved) |
| Doesn't fit any | escape-hatch | none — surface to user |
</question-shape-quick-reference>

</research-pattern-table>
