# Kipling Questions at the Code/Implementation Layer

Six universal categories with code-layer semantics. Each turn picks the subset that closes this turn's highest-value gap.

## Categories

| Kipling | Code-layer semantics | Typical question shapes |
|---|---|---|
| **What** | entities, types, data in touched code; new ones being added; field/shape changes | "What types exist?", "What new entity does this add?", "What changes in the wire schema?" |
| **How** | functions, methods, endpoints; control flow; call sites; new code's interaction shape | "How does X work today?", "How does the new flow compose with existing handlers?", "What's the call sequence?" |
| **Who** | callers, dependents, downstream consumers; ownership of touched modules | "Who calls this?", "Who depends on the current behavior?", "Who owns this module?" |
| **When** | events, triggers, hooks, lifecycle moments; timing, ordering; async/sync boundaries | "When does this fire?", "When is invariant X established?", "What's the ordering constraint?" |
| **Why** | invariants, constraints, error rules; ADRs/DRs touching the area; security/perf/compliance | "Why is this constraint here?", "Which invariant does the change touch?", "What did DR-NNN decide?" |
| **Where** | file, module, package locations; external integrations; cross-cutting code presence | "Where does this code live?", "Where are the integration points?", "Where else does this pattern apply?" |

## Per-tag emphasis matrix

The ticket's primary tag modulates which categories carry more weight this turn. The agent does not need to ask every category every turn — pick the heavy hitters per the tag.

| Primary tag | Emphasis order | Notes |
|---|---|---|
| `feature` | What → How → Where → Who → Why → When | All six matter. What and How are heaviest (new entities + new capabilities). |
| `bug` | Why → How → Who → Where → What → When | Why is heaviest (invariant violated). How second (call path that triggers). Who third (who depends on the broken behavior). |
| `exploration` | How → Why → What → Where → Who → When | How and Why heaviest (what could exist, what would break). |
| `hotfix` | Why → Where → How → … | Why heaviest (which invariant). Where second (smallest blast radius). Keep the surface tight. |
| `infrastructure` | Where → What → How → Why → Who → When | Where and What heaviest (where infra lives, what it manages). |
| `chore` | Often only 1-2 categories matter | Where for renames; How for refactors. Keep it minimal. |

## Grill-with-docs discipline (applied during each derivation)

- **Glossary challenge against CONTEXT.md**: if the ticket uses a term the codebase or CONTEXT.md uses differently, surface the conflict.
- **Sharpen fuzzy language**: propose precise canonical terms for vague/overloaded ticket terms.
- **Concrete-scenario stress-test**: invent specific scenarios that probe domain boundaries.
- **Code cross-reference**: verify ticket claims against actual code; surface contradictions.
- **Inline CONTEXT.md update**: capture new domain terms as they surface during Q↔R, not at session end.
- **Three-condition DR/ADR gate**: when Q-phase surfaces an architecturally-meaningful decision (hard to reverse + surprising without context + real trade-off), spawn a DR inline.
- **One question at a time via Question tool**: recommended answer first with "(Recommended)" suffix.

## What goes into the dispatch instructions

Per turn, the Kipling derivation produces a structure used in step 3:

```yaml
turn_questions:
  - kipling: How
    text: "How does authentication wire into the request pipeline today?"
    pattern: codebase-navigate
    scope: src/middleware/, src/routes/
  - kipling: Where
    text: "Where does the rate limiter live?"
    pattern: codebase-navigate
    scope: src/middleware/
  - kipling: Why
    text: "Why was the synchronous-HTTP boundary chosen between Ordering and Billing?"
    pattern: thoughts-navigate
    scope: thoughts/shared/decisions/
```

Cap at 4 questions per turn (matches the 4-subagent cap in research-pattern-table.md).
