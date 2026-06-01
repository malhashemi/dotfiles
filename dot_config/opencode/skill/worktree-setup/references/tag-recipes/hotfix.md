<tag-recipe name="hotfix">

<overview>
A `hotfix` ticket is an emergency fix. Production is broken (or near-broken), customer-impacting, blocking. Minimal ceremony — get the fix shipped, document after.
</overview>

<depth-expectations>
| Phase | Depth |
|---|---|
| Q↔R | 1-2 turns; just enough to confirm reproduction and scope |
| D | Fix approach + rollback plan only |
| S | Minimal flat section list |
| P | Trivial: fix → test → ship |
| I | 100-300 lines typical |
| V | Self-review only; no subagent dispatch (speed matters for hotfix) |
</depth-expectations>

<mandatory-sections>
1. **Incident Description** — what's broken; impact (which customers, which severity, when started); link to incident channel or report
2. **Fix** — the specific change being made (still WHAT, not HOW — but more focused than feature)
3. **Rollback Plan** — how to back out the fix if it makes things worse
4. **Verification** — how the fix will be verified before declaring incident resolved
5. **Postmortem Link** — wiki-link to the planned (or completed) postmortem document
</mandatory-sections>

<optional-sections>
- **Root Cause** — if known at time of writing; often deferred to postmortem
- **Workaround in Effect** — what's keeping the service running until the fix lands
- **Affected Systems** — broader blast radius beyond the immediate symptom
- **Decision Records** — rarely needed for hotfix; only if a hard-to-reverse decision is made under duress (e.g., feature flag flip, vendor switch)
</optional-sections>

<ac-patterns>
Hotfix ACs are **incident-resolution-focused**:

- "Reported failure mode no longer occurs in production."
- "Customer-facing impact has been verified resolved by [team / monitoring / direct test]."
- "Rollback plan has been tested or otherwise validated as workable."
- "Postmortem ticket created (link in Postmortem Link section)."

Hotfix ACs are LESS comprehensive than feature ACs — the goal is "stop the bleeding", not "comprehensively prove correctness." Comprehensive correctness comes in follow-up work post-incident.
</ac-patterns>

<common-pitfalls>
- **Hotfix scope creep**: under pressure, the team adds "while we're shipping a fix, also..." improvements. Discipline: hotfix is MINIMAL. Improvements belong in follow-up tickets.
- **Missing rollback**: shipped without a rollback is shipping blind. Always have a back-out path.
- **No postmortem link**: incidents without postmortems repeat. Link the planned postmortem ticket even if it's not yet written; create the placeholder ticket alongside this hotfix.
- **Insufficient verification**: "looks good in dev" is not verification for production. The Verification section names what evidence will signal success in production (monitoring metric, customer report, direct test).
- **Misuse for non-urgent work**: hotfix tag is for genuinely urgent customer-impacting work. Routine bug fixes use the bug tag, not hotfix.
</common-pitfalls>

<q-r-focus-areas>
When grilling a hotfix:
- What's broken right now?
- Who's impacted? (customer scope, internal team scope, blast radius)
- What's the workaround keeping things running?
- What's the minimum change to fix this?
- How will we know it worked?
- How do we back out if it makes things worse?
- Is there a follow-up postmortem planned?

Q↔R should be FAST. Hotfix work is time-sensitive. If Q↔R takes more than 30 minutes, the work might not actually be a hotfix.
</q-r-focus-areas>

<length-estimate>
Typical hotfix ticket: 100-300 lines. Trivial hotfixes (config flip, single-line code fix): 80-150. Larger emergency fixes that span multiple systems: 300-500.

If a hotfix is estimated at 500+ lines, the work is probably better tagged as bug (urgent but not emergency) or feature (full ceremony).
</length-estimate>

<branch-prefix>
Single plan: `hotfix/{ticket-slug}`
Multi-plan:  `hotfix/{ticket-slug}-plan-{n}`
</branch-prefix>

</tag-recipe>
