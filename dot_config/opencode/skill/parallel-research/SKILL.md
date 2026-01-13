---
name: parallel-research
description: |
  Research scope too big? This skill decomposes large questions into independent parts, spawns 
  parallel researchers, and synthesizes findings. Essential when comprehensive research would 
  overflow a single context window.
---

# Parallel Research

## Overview

When research scope is large, decompose into independent questions and spawn parallel 
researchers. This skill turns a single researcher into a research coordinator.

## When to Use

- When research question spans multiple distinct domains
- When research would exceed context window if done sequentially
- When independent aspects can be researched concurrently
- When RPIV or Planner requests broad research coverage

## Decomposition Criteria

A research question should be decomposed when:

| Criterion | Threshold | Example |
|-----------|-----------|---------|
| Topic breadth | 3+ distinct areas | "Research auth, caching, AND API patterns" |
| Estimated context | >50% for single researcher | Large codebase analysis |
| Independence | Aspects don't depend on each other | Security review vs performance review |

A research question should NOT be decomposed when:

- Topics are deeply interrelated
- Sequential discovery is required (A informs B)
- Total scope fits in single context window

## Decomposition Process

### Step 1: Analyze Research Scope

Parse the research request to identify:
- Core questions that must be answered
- Independent aspects that can be parallelized
- Dependencies between aspects (if any)

### Step 2: Design Research Questions

For each independent aspect, create a focused research question:

```markdown
## Research Question: [Aspect Name]

**Focus**: [Specific scope - what to research]
**Boundaries**: [What NOT to research - stay focused]
**Output**: [Expected deliverable format]
**Context needed**: [What context to provide]
```

### Step 3: Spawn Parallel Researchers

Use the Task tool to spawn researchers:

```
task({
  subagent_type: "researcher",
  description: "Research [aspect name]",
  prompt: "Research Question: [question]
           Focus: [scope]
           Boundaries: [limits]
           Output format: [expected format]
           
           Return findings as structured Markdown with file:line references."
})
```

Spawn all independent researchers simultaneously by issuing multiple Task calls in parallel.

### Step 4: Collect Results

As each researcher returns:
1. Validate the response addresses the question
2. Extract key findings
3. Note any cross-references or dependencies discovered

### Step 5: Synthesize Findings

Combine all research into a unified output:

```markdown
# Research Synthesis: [Original Topic]

## Executive Summary
[High-level findings across all research tracks]

## Detailed Findings

### [Aspect 1 Name]
[Synthesized findings from Researcher 1]
- Key discovery 1 (file:line)
- Key discovery 2 (file:line)

### [Aspect 2 Name]
[Synthesized findings from Researcher 2]
- Key discovery 1 (file:line)
- Key discovery 2 (file:line)

## Cross-Cutting Themes
[Patterns or connections discovered across research tracks]

## Recommendations
[Actionable next steps based on findings]

## References
[All file:line references from all researchers]
```

## Output to Parent

When research is complete, return to orchestrator (RPIV or Planner):

```
RESEARCH_COMPLETE
Topics researched: N
Key findings:
  - [Finding 1]
  - [Finding 2]
Full synthesis: [path to research doc]
```

## Error Handling

- **Researcher fails**: Continue with other researchers, note gap in synthesis
- **Context overflow in child**: Accept partial findings, note limitation
- **Conflicting findings**: Document both perspectives, flag for human review
