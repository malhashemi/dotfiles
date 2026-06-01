<research-document-format>

<overview>
The persistence contract for research documents produced by the
researcher's persisting skills (Comprehensive Investigation, Focused
Study, Scout External Codebase, Risk Reconnaissance). A research
document is a load-bearing artifact downstream consumers act on — its
frontmatter is queryable, its citations are navigable, its gaps are
honest.
</overview>

<location>
Write to the session's research directory: run `thoughts metadata` to
resolve `shared_folder`, then write to `{shared_folder}/research/`.
Filename: `YYYY-MM-DD_HH-MM-SS_{topic-slug}.md` (timestamp from
thoughts metadata; slug is a kebab-case reduction of the topic).
</location>

<frontmatter>
Every research document opens with this YAML frontmatter. Values come
from `thoughts metadata`; never use placeholders.

```yaml
---
date: {ISO 8601 timestamp with timezone}
researcher: {owner from thoughts metadata}
git_commit: {current commit hash}
branch: {current branch}
repository: {repo name}
topic: "{the research question / topic}"
tags: [research, {methodology}, {relevant-component-or-domain-tags}]
status: complete
last_updated: {YYYY-MM-DD}
last_updated_by: {owner}
---
```
</frontmatter>

<body-skeleton>
After frontmatter, the body opens with these fixed sections; the middle
sections come from the selected investigation methodology.

```markdown
# Research: {topic}

**Date**: {timestamp}
**Researcher**: {owner}
**Git Commit**: {commit}
**Branch**: {branch}
**Repository**: {repo}

## Research Question

{the original question, verbatim}

## Summary

{high-level findings answering the question — 1-2 paragraphs}

{methodology-specific sections here — see investigation-methodologies}

## Open Questions

{what the evidence could not answer; honest gaps}
```
</body-skeleton>

<citation-rule>
Every claim in the body carries an inline citation: `file:line`, a URL,
or a `thoughts/` alias. A claim without a citation is an opinion, and
opinions do not belong in a research document. Negative findings are
cited too ("searched {scope}; no match — codebase-locator returned
zero results").
</citation-rule>

<permalink-rule>
When the current commit is pushed (on a branch with an upstream, or on
the default branch), convert local `file:line` references to GitHub
permalinks: resolve owner/repo via `gh repo view --json owner,name`,
build `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.
When the commit is not pushed, keep local `file:line` references —
a dangling permalink is worse than an honest local path.
</permalink-rule>

<path-handling>
When citing files discovered under a `thoughts/searchable/` hardlink
mirror, document the path with `searchable/` removed and every other
segment preserved: `thoughts/searchable/shared/prs/123.md` becomes
`thoughts/shared/prs/123.md`. Never rewrite the owner segment (personal
vs shared).
</path-handling>

<sync-rule>
After writing the document, run `thoughts sync` so the artifact is
indexed and available to thoughts-locator on future investigations.
</sync-rule>

<follow-up-rule>
A follow-up on an existing investigation appends to the SAME document:
add a `## Follow-up: {date}` section, update `last_updated` and
`last_updated_by`, and add `last_updated_note` to the frontmatter. Do
not spawn a second document for a continuation of the same question.
</follow-up-rule>

</research-document-format>
