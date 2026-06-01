<verification-angle-table>

<overview>
The codesmith V-phase runs 5 verification gates. Each gate runs a mandatory angle set plus conditional angles triggered by ticket tags or I-phase signals.
</overview>

<gates>
| # | Gate | Position |
|---|---|---|
| 1 | D-review | After D, before S |
| 2 | P-review | After P, before Work-Tree |
| 3 | I-per-slice | After each I-phase slice |
| 4 | final-integration | After all slices verified |
| 5 | PR-review | After PR opened (conditional on PR mode) |
</gates>

<mandatory-angles-matrix>
| Angle | D-review | P-review | I-per-slice | final-integration | PR-review |
|---|---|---|---|---|---|
| `plan-adherence` | — | ✓ (to design) | ✓ (to plan) | ✓ (full) | ✓ |
| `code-quality` | — | — | ✓ | ✓ | ✓ |
| `test-quality` | — | — | ✓ | ✓ | ✓ |
| `architecture` | ✓ | — | — | ✓ | ✓ |
| `sizing` | ✓ | ✓ | — | — | — |
| `completeness-vs-ac` | — | ✓ | — | ✓ | ✓ |
</mandatory-angles-matrix>

<conditional-angles>
| Angle | Trigger |
|---|---|
| `security` | Primary tag is `feature` or `hotfix`; OR secondary tag includes `security`; OR I-phase signaled an auth/credential/data-exposure code path |
| `performance` | Secondary tag includes `performance`; OR I-phase signaled a hot-path |
| `compliance` | Secondary tag includes `compliance`; OR touched code is in a regulated module per ADR |
| `operational` | Primary tag is `infrastructure`; OR I-phase touched logging / monitoring / error paths |
| `documentation` | Every slice if CONTEXT.md was touched; otherwise final-integration only |
| `dependency` | P or I added/modified package.json / Cargo.toml / pyproject.toml / equivalent |
</conditional-angles>

<mechanism-per-angle>
Fitness functions run FIRST, in parallel. LLM angles run only after fitness functions pass for that angle's two-pass cases.

| Angle | Mechanism |
|---|---|
| `plan-adherence` | LLM |
| `code-quality` | fitness function (linter / static analysis), then LLM (logic / pattern reasoning) |
| `test-quality` | LLM |
| `security` | fitness function (CVE scan + secret detection), then LLM (logic-level vulns) |
| `architecture` | fitness function (module-boundary rules from ADR), then LLM (harder seam questions) |
| `performance` | fitness function (benchmark regression detection), then LLM (algorithmic complexity) |
| `documentation` | LLM |
| `operational` | fitness function (logging/telemetry hook existence), then LLM (adequacy) |
| `compliance` | fitness function (declared compliance checks), then LLM (harder cases) |
| `dependency` | fitness function (manifest check), then LLM ("is this dep allowed by ADRs?") |
| `sizing` | LLM |
| `completeness-vs-ac` | LLM |

When a fitness function fails, the gate is BLOCKED at the relevant severity (typically High or Critical depending on the failure). LLM angles for that gate may still run for completeness, but they do not change the verdict.
</mechanism-per-angle>

<loop-back-routing>
When BLOCKED, the validator's JSON output MUST set `loop_back_target`.

| Root cause | Loop back to |
|---|---|
| Code bug, missing test, pattern violation | `I-phase` |
| Plan slice wrong-sized, wrong order, missing step | `P-phase` |
| Plan missing scope, declared_files wrong | `P-phase` (often loops further back to `S-phase` if structure was wrong) |
| Structural file/signature/test-file decision wrong | `S-phase` |
| Design approach wrong | `D-phase` |

A BLOCKED verdict in the execution session with `loop_back_target: D-phase` is an abort condition. Halt; surface to user; recommend restarting the planning session.
</loop-back-routing>

<codebase-wide-scope-marker>
Findings flagged `scope: codebase-wide` accumulate in the verification doc but do not block this implementation's verdict. They are signals to a separate codebase-review workflow.
</codebase-wide-scope-marker>

</verification-angle-table>
