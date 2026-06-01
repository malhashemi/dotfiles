---
name: context-md-format
description: "Authoring spec for CONTEXT.md and CONTEXT-MAP.md. Load this when you are about to write to or update a project's vocabulary glossary. Defines glossary-only scope, the single-vs-multi-context layout, opinionated naming rules, the file template, the lazy-create policy, and the inline-update discipline. Reader-side awareness (when to read CONTEXT.md, how to use canonical terms) lives in the shared baseline — see `shared/baseline/context-md-awareness.md`. This skill is the authoring counterpart, loaded only by agents with write authority."
---

# CONTEXT.md Authoring Format

This is the authoring spec for the project vocabulary glossary at `CONTEXT.md` (single-context) or `CONTEXT-MAP.md` + per-context `CONTEXT.md` files (multi-context). Reader-side awareness — when to read it, how to honor canonical terms, why most agents do NOT write to it — lives in the shared baseline at `shared/baseline/context-md-awareness.md`. Load this skill only when you have write authority and are about to edit.

## Scope

`CONTEXT.md` is **glossary only**. It is NOT a spec. It is NOT a scratchpad. It is NOT an implementation log. It is a tight list of terms with one-sentence definitions, plus relationships and an example dialogue that demonstrates correct usage.

Term inclusion rule: **only terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) do not belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this project, or a general programming concept? Only the former belongs.

## CONTEXT.md Template

```md
# {Context Name}

{One or two sentences describing what this context is and why it exists.}

## Language

**Order**:
A concise description of the term.
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account

## Relationships

- An **Order** produces one or more **Invoices**
- An **Invoice** belongs to exactly one **Customer**

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."

## Flagged ambiguities

- "account" was used to mean both **Customer** and **User** — resolved: these are distinct concepts.
```

## CONTEXT-MAP.md Template (multi-context only)

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md) — generates invoices and processes payments
- [Fulfillment](./src/fulfillment/CONTEXT.md) — manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing**: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing**: Shared types for `CustomerId` and `Money`
```

## Authoring Rules

1. **Be opinionated.** When multiple words exist for the same concept, pick the best one as canonical and list the others as aliases to avoid with `_Avoid_`.
2. **Flag conflicts explicitly.** If a term is used ambiguously, call it out in the "Flagged ambiguities" section with a clear resolution sentence.
3. **Keep definitions tight.** One sentence maximum per term. Define what it IS, not what it does.
4. **Show relationships.** Use bold term names. Express cardinality where obvious (one Order produces many Invoices; an Invoice belongs to exactly one Customer).
5. **Only project-specific terms.** General programming concepts do not belong.
6. **Group under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat `## Language` list is fine.
7. **Write an example dialogue.** A short conversation between a dev and a domain expert that demonstrates how the terms interact naturally. The dialogue clarifies boundaries between related concepts that bare definitions cannot.

## Lazy-Create Policy

Do NOT create `CONTEXT.md` preemptively. Create it the moment the first term is resolved during a grilling session.

The first time a grilling exchange produces a term-meaning pair worth recording (e.g., user clarifies "by 'workspace' I mean a team-scoped container, not a UI panel"):

1. Create `CONTEXT.md` at the resolved glossary location — `{shared_folder}/CONTEXT.md` in a thoughts-mapped repo (run `thoughts metadata` to resolve `shared_folder`), otherwise the repo root — with the template above. In a thoughts-mapped repo, prepend minimal thoughts frontmatter (a non-actionable `kind` such as `note`, a terminal `status`, and `aliases`) so the file passes `thoughts validate` and never surfaces in the backlog.
2. Fill in the project name and a one-sentence project description.
3. Add the first term under `## Language`.
4. Continue the grilling exchange.

For subsequent resolved terms in the same session, append to the existing file inline — do not batch updates until session end. The principle: capture terms as they crystallize, not as a separate "documentation pass."

## When to Promote to a Multi-Context Layout

Single-context is the default. Promote to multi-context only when:

- The codebase has genuinely separate bounded contexts that own different vocabularies (e.g., Ordering vs Billing in an e-commerce app).
- A term means meaningfully different things in different parts of the system.
- The list of terms in a single `CONTEXT.md` has grown past ~25 entries AND they cluster naturally into 2+ groups.

Promotion is a deliberate refactor: split the existing `CONTEXT.md` into per-context files, create `CONTEXT-MAP.md` at the resolved glossary location, update any agent prompts that hardcode a glossary path. Treat as a Decision Record if hard-to-reverse.

## What CONTEXT.md Is NOT

- **Not a spec.** Specs live in `thoughts/shared/specs/`. CONTEXT.md captures vocabulary; specs capture contracts.
- **Not implementation notes.** Implementation lives in code and in `thoughts/shared/implementations/`. CONTEXT.md does not describe HOW the system works.
- **Not a glossary of general programming terms.** "API", "middleware", "promise" do not belong unless they have project-specific meaning that diverges from the general definition.
- **Not historical.** When a term is renamed or retired, update the entry inline. Old usage is preserved in git history. Do not keep a "deprecated terms" section unless the deprecation is actively in progress.
