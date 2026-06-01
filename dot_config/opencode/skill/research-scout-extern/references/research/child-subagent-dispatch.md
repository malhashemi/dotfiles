<child-subagent-dispatch>

<overview>
Maps the shape of a research question to the child subagent best suited
to answer it. Used by the researcher's skills to select which of the six
read-only research children to dispatch. Dispatch is question-driven:
the shape of what's being asked selects the child, not the domain of the
parent task.
</overview>

<table>

| Question shape | Child subagent | Notes |
|---|---|---|
| "Does X exist? / where does X live?" | `codebase-locator` | File paths and locations. Fast, surface-level. |
| "How does X work today?" | `codebase-analyzer` | Behavior, control flow, integrations. Deeper than locator. |
| "Is there a pattern for X? / how have we done X before?" | `codebase-pattern-finder` | Existing implementations to model after; concrete code examples. |
| "Have we discussed X? / is there a prior doc on X?" | `thoughts-locator` | Finds candidate prior artifacts in thoughts/ (tickets, research, plans, PRs). |
| "What did that prior doc decide about X?" | `thoughts-analyzer` | Deep extraction from a known thoughts/ artifact. Names the artifact path or the candidates a prior locator surfaced. |
| "What do other systems do for X? / external docs on X?" | `web-search-researcher` | Public sources. Requires caller approval before dispatch. |

</table>

<two-stage-thoughts>
"Have we discussed X?" is two-stage when the artifact is unknown:
thoughts-locator finds candidates, then thoughts-analyzer reads the
selected ones. When the artifact path is already known, dispatch
thoughts-analyzer directly against that path.
</two-stage-thoughts>

<smallest-set>
Choose the smallest set of children that covers the question's shapes.
A single-shape question dispatches one child. A multi-shape question
("what do we have, how have we solved it before, and how do others?")
dispatches one child per shape, in parallel. Do not dispatch extra
children to look thorough — each dispatch costs context and wall-clock,
and child quality degrades with vague prompts.
</smallest-set>

<prompt-anatomy>
Every child prompt names exactly:
1. WHAT to find — the question text
2. WHERE to look — the scope (directory globs, file paths, or domain)
3. CONSTRAINTS — e.g., "locate only, do not analyze" (when specified)
4. OUTPUT SHAPE — e.g., "markdown table of file:line with one-line purpose"

The child prompt carries the question alone — never the parent task's
intent. A child gathers better facts when it does not know what
conclusion is wanted.
</prompt-anatomy>

<direct-read-instead>
Some questions are answered by reading a known file directly (bundle
files, thoughts/ artifacts at a known path, root-level docs). Those
need no child dispatch — read directly. Child dispatch is for codebase
search, prior-thoughts discovery, and web research.
</direct-read-instead>

</child-subagent-dispatch>
