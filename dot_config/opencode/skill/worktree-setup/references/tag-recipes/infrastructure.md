<tag-recipe name="infrastructure">

<overview>
An `infrastructure` ticket sets up, changes, or removes plumbing. Build tooling, CI/CD, deployment, dependency management, observability, dev environment. Not user-facing behavior; cross-cutting concern. Medium depth — comparable to feature in ceremony but different in content focus.
</overview>

<depth-expectations>
| Phase | Depth |
|---|---|
| Q↔R | 3-6 turns; setup/config implications often need probing |
| D | Setup-step mapping + dependencies + verification strategy |
| S | Flat or numbered Parts depending on scope breadth |
| P | Ordered setup steps; checkpoints at key transitions |
| I | 400-1000 lines typical |
| V | Self-review + ticket-reviewer subagent dispatch (mandatory per spec §10.1) |
</depth-expectations>

<mandatory-sections>
1. **Current State** — what infrastructure exists now (or doesn't); the baseline
2. **Target State** — what infrastructure should exist after this ticket; the desired end-state
3. **Setup Steps Required** — ordered list of WHAT must be configured/installed/changed (WHAT, not HOW)
4. **Dependencies** — upstream packages, services, vendors, or accounts this work depends on
5. **Verification** — how to confirm the infrastructure is set up correctly (commands to run, metrics to check, behaviors to observe)
6. **Acceptance Criteria** — testable end-state behaviors
7. **Rollback Plan** — how to back out if the infrastructure change breaks things
8. **Out of Scope** — adjacent infrastructure that might seem related but is separate
</mandatory-sections>

<optional-sections>
- **Security Considerations** — credential management, access control, secret rotation
- **Cost Implications** — when infrastructure has meaningful $ impact
- **Migration / Cutover** — when switching from existing infrastructure to new
- **Monitoring / Observability** — what metrics or alerts come with this setup
- **Decision Records** — vendor choice, architecture pattern, technology choice all qualify
</optional-sections>

<ac-patterns>
Infrastructure ACs are **state-verifying**:

- "Running `terraform plan` produces no diff (infrastructure matches code)."
- "CI pipeline build step `lint` exits with status 0 for all PR-targeted commits."
- "Health endpoint /healthz returns 200 in production after rollout."
- "All previously-passing tests still pass after the dependency upgrade."
- "New deployment region serves traffic with <p99=500ms latency."

ACs name VERIFIABLE STATES of the infrastructure — not implementation details but observable correctness signals.
</ac-patterns>

<common-pitfalls>
- **Skipping rollback plan**: infrastructure changes can take down production. Always have a rollback path.
- **Verification by intuition**: "looks right" is not verification. Name the specific commands, metrics, or behaviors that confirm success.
- **Hidden dependencies**: an infrastructure change often touches more than expected (e.g., a CI tool upgrade may require updating Docker base images). Q↔R should probe for dependency chain.
- **Cost surprises**: cloud infrastructure changes can balloon costs. If the change has $ implications, surface in Cost Implications.
- **Missing security review**: credential, network, and access changes need security review. Don't skip even when "it's just internal infra."
- **Misuse for code refactors**: a refactor without behavior change is still feature-tier in many cases. Infrastructure is genuinely about plumbing — CI, deployment, build, dev tools.
</common-pitfalls>

<q-r-focus-areas>
When grilling infrastructure:
- What state does the infrastructure exist in NOW?
- What state should it exist in AFTER?
- What are the steps to get from one to the other?
- What dependencies (other systems, packages, accounts, services) are required?
- How will we verify the setup is correct?
- How will we back out if it breaks something?
- What's the blast radius if it goes wrong?
- Are there security or cost implications?
</q-r-focus-areas>

<dr-opportunities>
Infrastructure tickets often spawn DRs because the work involves hard-to-reverse decisions:
- Vendor choice (which CI provider, which CDN, which secret manager)
- Architecture pattern (centralized config vs distributed, push vs pull, mesh vs gateway)
- Technology choice (Terraform vs Pulumi vs CloudFormation; Kubernetes vs serverless)
- Boundary decision (which team owns this infrastructure)

Each of these typically passes the three-condition gate (hard to reverse, surprising without context, real trade-off) — surface during Q↔R.
</dr-opportunities>

<length-estimate>
Typical infrastructure ticket: 400-800 lines. Small infrastructure changes (single config tweak): 200-400. Large infrastructure work (new region, new service tier): 800-1500.

Beyond 1500 lines suggests the work should decompose downstream into multiple sub-tickets (e.g., "set up new region" decomposes into "provision network → provision services → cutover").
</length-estimate>

<branch-prefix>
Single plan: `infra/{ticket-slug}`
Multi-plan:  `infra/{ticket-slug}-plan-{n}`
</branch-prefix>

</tag-recipe>
