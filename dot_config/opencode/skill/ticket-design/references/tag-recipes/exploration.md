<tag-recipe name="exploration">

<overview>
An `exploration` ticket investigates an open question. Spike, learning goal, evaluation of alternatives. The output is INFORMATION (a decision, a recommendation, a documented finding) — not a feature, not a fix. Time-boxed by design.
</overview>

<depth-expectations>
| Phase | Depth |
|---|---|
| Q↔R | 3-6 turns; question-formulation is the main activity |
| D | Lightweight — designing the SPIKE shape, not a feature chain |
| S | Spike-output-shaped section list |
| P | Time-boxed plan; subagent dispatch for research |
| I | 300-600 lines typical |
| V | Self-review + ticket-reviewer subagent dispatch (mandatory per spec §10.1) |
</depth-expectations>

<mandatory-sections>
1. **Goal** — what question is being explored; what decision will be informed by the answer
2. **Boundaries** — what's IN the spike (specific question, specific scope) and what's OUT (not a full implementation, not a production-ready solution)
3. **Time Box** — how much time the spike has (hours, days); when to stop and report findings even if incomplete
4. **Expected Outputs** — what artifacts the spike will produce (research doc, prototype, recommendation, decision document)
5. **Decision Points** — what the user (or downstream agent) will decide based on the spike's findings
6. **Acceptance Criteria** — when is the spike "done"? (typically: question answered to a degree that supports the decision, OR time box reached)
7. **Out of Scope** — what this spike does NOT investigate (adjacent questions, full implementation, scaling concerns, etc.)
</mandatory-sections>

<optional-sections>
- **Hypothesis** — the agent's current best guess at the answer; the spike validates or refutes it
- **Prior Art** — existing research, briefs, or thoughts/ artifacts that inform the question
- **Prototype Strategy** — if Q↔R surfaced a prototyping opportunity (LOGIC or UI)
- **Risk** — the cost of NOT exploring (decision blocked, wrong assumption persists)
</optional-sections>

<ac-patterns>
Exploration ACs are **decision-supporting**:

- "Question X is answered with a defensible recommendation (yes/no/conditional)."
- "Research doc captures findings with evidence (file paths, URLs, benchmarks)."
- "Decision Record drafted if the spike concludes with a hard-to-reverse choice."
- "If time box was reached without a full answer, the partial findings are documented along with the next-step recommendation."

Spikes can ACCEPTABLY fail — "we explored and the question is harder than expected; here's what we learned and what to do next" is a valid outcome.
</ac-patterns>

<common-pitfalls>
- **Scope creep into implementation**: spikes start as questions and drift into building. Time box is the discipline; when it's reached, STOP and report. Don't ship spike code to production.
- **Ambiguous decision point**: if the spike's findings don't clearly inform a decision, the goal was too fuzzy. Refine the goal during Q↔R: what specific DECISION will this spike enable?
- **No time box**: open-ended spikes never end. Always set a time box, even if rough.
- **Outputs forgotten**: spike findings are LOST if not captured in a durable artifact. Mandatory: research doc updates, optional DR.
- **Tag misuse**: features sometimes get tagged exploration to dodge the heavier feature ceremony. Catch in step 5 of ticket-orient: if the work IS adding capability, it's a feature, not an exploration.
</common-pitfalls>

<q-r-focus-areas>
When grilling an exploration:
- What specific question are we answering?
- What decision will this answer enable?
- How much time should this take (rough order of magnitude)?
- What's the lightest possible artifact that answers it?
- Is there a prototype that would answer this faster than research?
- Who needs to see the result?
</q-r-focus-areas>

<prototype-invocation>
Exploration tickets are the most natural fit for the ticket-prototype skill (Lock 38). If the question is answerable by running throwaway code, the Q↔R loop should invoke ticket-prototype during a turn. The prototype's findings absorb into the research file; the spike's output references them.
</prototype-invocation>

<length-estimate>
Typical exploration ticket: 300-600 lines. Small spikes (1-day investigations): 200-400. Larger spikes with multiple prototypes or evaluations: 600-900.

Beyond 900 lines suggests the spike is actually a feature-shaped piece of work — consider re-tagging.
</length-estimate>

<branch-prefix>
Single plan: `spike/{ticket-slug}`
Multi-plan:  `spike/{ticket-slug}-plan-{n}`
</branch-prefix>

</tag-recipe>
