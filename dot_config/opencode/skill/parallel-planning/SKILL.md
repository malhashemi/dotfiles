---
name: parallel-planning
description: |
  Planning multiple workstreams? This skill identifies independent workstreams, spawns parallel 
  planners, and analyzes dependencies between resulting plans. Perfect for large features 
  spanning multiple components.
---

# Parallel Planning

## Overview

When planning scope is large, identify independent workstreams and spawn parallel planners.
Analyze dependencies between resulting plans to determine execution order.

## When to Use

- When implementation spans multiple independent components
- When different expertise areas are needed (backend vs frontend vs infrastructure)
- When parallel implementation tracks are possible
- When RPIV identifies multiple workstreams from research

## Decomposition Criteria

Planning should be parallelized when:

| Criterion | Threshold | Example |
|-----------|-----------|---------|
| Component count | 3+ independent components | API, CLI, and database changes |
| Expertise domains | 2+ distinct domains | Security hardening + UX improvements |
| Team boundaries | Work could be done by different people | Core library + integration layer |

Planning should NOT be parallelized when:

- Components are tightly coupled
- Sequential design decisions required
- Total scope fits single plan

## Decomposition Process

### Step 1: Identify Workstreams

From research documents, identify:
- Independent components or systems
- Distinct capability areas
- Natural boundaries in the codebase

### Step 2: Define Workstream Briefs

For each workstream, create a planning brief:

```markdown
## Workstream: [Name]

**Scope**: [What this workstream covers]
**Research inputs**: [Relevant sections from research]
**Constraints**: [Dependencies, limitations]
**Expected phases**: [Rough estimate]
**Output**: Implementation plan document
```

### Step 3: Spawn Parallel Planners

Use Task tool with planner subagent:

```
task({
  subagent_type: "planner",
  description: "Plan [workstream name]",
  prompt: "Create implementation plan for workstream: [name]
           
           Scope: [scope]
           Research: [research summary]
           Constraints: [constraints]
           
           Follow standard plan format with phases, success criteria, and file:line references.
           Return path to completed plan document."
})
```

### Step 4: Analyze Dependencies

When all planners return:

1. Read each plan's phases
2. Identify cross-plan dependencies:
   - Does Plan A's Phase 2 require Plan B's Phase 1?
   - Are there shared files that create conflicts?
   - Do plans make conflicting assumptions?

3. Create dependency graph:

```markdown
## Dependency Analysis

### Execution Order
1. Plan A: Phases 1-2 (no dependencies)
2. Plan B: Phases 1-3 (depends on A.Phase2)
3. Plan A: Phases 3-4 (can parallel with B)
4. Plan C: All phases (independent, full parallel)

### Conflicts Identified
- Plan A and B both modify `src/config.ts` in Phase 2
  - Resolution: Execute A.Phase2 first, B.Phase2 after

### Parallelization Opportunities
- Plan C can run entirely in parallel with A+B
- Plan A.Phase3 and B.Phase2 can run in parallel
```

### Step 5: Create Execution Plan

Synthesize findings into execution recommendation:

```markdown
# Execution Plan

## Plans Created
1. [Plan A path] - [summary]
2. [Plan B path] - [summary]
3. [Plan C path] - [summary]

## Recommended Execution Order

### Wave 1 (Parallel)
- Plan A: Phases 1-2
- Plan C: All phases (independent)

### Wave 2 (Sequential)
- Plan B: Phases 1-3 (after Plan A.Phase2)

### Wave 3 (Parallel)
- Plan A: Phases 3-4
- (Plan C already complete)

## Risk Assessment
- [Risk 1]: [Mitigation]
- [Risk 2]: [Mitigation]
```

## Output to RPIV

When planning is complete:

```
PLANNING_COMPLETE
Plans created: N
Execution waves: M
Key dependencies:
  - [Plan dependency 1]
  - [Plan dependency 2]
Full execution plan: [path to execution plan doc]
```

## Error Handling

- **Planner fails**: Gather partial work, note gap, may need manual planning
- **Conflicting plans**: Document conflicts, escalate to RPIV for resolution
- **Circular dependencies**: Flag as blocking issue, require human input
