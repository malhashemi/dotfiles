<!-- ================================================================
     TEMPLATE: subagent-instructions
     PURPOSE:  The body of a subagent's instructions file. Defines what
               the subagent receives at dispatch and how it executes.
     REQUIRED: Subagents only. Primary agents do NOT use this template
               (their body is the activation block + persona + menu).
     USED BY:  Compiled INTO the subagent's instructions.md file,
               placed after persona.md in the agent.yaml includes list.

     STRUCTURE OVERVIEW:
       A subagent's body has exactly TWO top-level XML sections:
         1. <input-expectations> — the structured dispatch contract
         2. <workflow>           — how the subagent executes + what it returns

       The body does NOT have a <scope> tag. Capability boundaries
       (what the subagent does and does not do) live in three places:
         - Hard prohibitions → frontmatter.md permission map (runtime-enforced)
         - Affirmative stance → persona.md <principles> (priors activation)
         - Operational discipline → workflow <step>/<action> content

       The body does NOT have an <identity>/<context>/<communication_style>
       tag — those live in persona.md (same 4-tag shape as primary agents).
       Read references/templates/persona.md first; this template assumes
       the persona is already drafted.
     ================================================================ -->

<input-expectations>
  <!-- FILL: input-expectations description
       1-2 sentences describing what the dispatching agent provides and
       in what shape. The dispatching agent reads this to know what to
       pack into its dispatch prompt.
       
       Example:
         "The dispatching agent (typically code-implement's step 3)
          spawns this subagent with a prompt containing the following
          fields. All required fields must be present; the subagent
          returns an error if any required field is missing."
  -->
  <description>
  </description>

  <!-- FILL: <input> entries
       Each input gets its own <input> tag with attributes:
         - name="snake_case_identifier" (required)
         - type="string|path|enum|json|integer|boolean" (required)
         - required="true|false" (required)
         - values="comma,separated,list" (optional; for enum types)
       
       The element content describes what the input IS and how it's used.
       Keep descriptions to 1-3 sentences. Be precise about format
       expectations (absolute path vs relative? wikilink vs alias? etc.).
       
       Examples:
         <input name="ticket_path" type="path" required="true">
           Absolute path to the draft ticket markdown file. The subagent
           reads this file completely before producing findings.
         </input>
         
         <input name="primary_tag" type="enum" required="true"
                values="feature,exploration,infrastructure">
           Which tag recipe applies. Determines severity calibration —
           feature tickets are reviewed for completeness vs AC;
           infrastructure tickets are reviewed for rollback criteria.
         </input>
         
         <input name="optional_context" type="string" required="false">
           Any additional notes the dispatching agent provides
           (e.g., specific concerns to focus on).
         </input>
  -->
  <input name="" type="" required="">
  </input>
</input-expectations>

<workflow>
  <!-- FILL: workflow content
       The workflow tag is where the subagent's HOW lives. It uses the
       same tag vocabulary as skill workflows (see shared/workflow-engine.md
       for the complete tag list), even though subagent instructions are
       NOT executed by the workflow engine directly — the tags carry
       structure for the reading LLM, which interprets them naturally
       because they match the engine's tag set used elsewhere.

       TWO PATTERNS based on agent capability:

       ==========================================================
       PATTERN A — Single-capability subagent (embedded workflow)
       ==========================================================
       Use when the subagent does ONE focused task. The workflow is
       embedded XML steps. Step 1 is ALWAYS Validate Dispatch — emits
       ERROR if inputs are missing or malformed. Phased steps decompose
       into substeps (see PHASED STEPS WITH SUBSTEPS below). Output
       format lives inside the final step as <check>-branched
       <output-format> blocks (see RETURN-SIGNAL MULTIPLICITY below).

         <workflow>
           <step n="1" title="Validate Dispatch">
             <action>
               Verify all required inputs present and well-formed
               (paths exist, enums match valid values, JSON arrays
               are non-empty). If missing or malformed, emit:

                 ERROR: Missing or malformed dispatch field '{field}'.
                 The dispatching orchestrator failed to supply complete
                 dispatch context. No work performed.

               And stop.
             </action>
           </step>

           <step n="2" title="Read All Bundle Files">
             <action>Read ticket_path, research_path, qa_log_path
                     completely. No skimming.</action>
           </step>

           <step n="3" title="Cross-Reference Decision Records">
             <substep n="3a" title="Resolve and Read Each DR">
               <action>Resolve each DR alias from ticket.children to
                       its file path. Read each DR completely.</action>
             </substep>
             <substep n="3b" title="Verify Decisions Match">
               <action>For each decision referenced in the ticket
                       body, verify it matches the DR record. Surface
                       drift as a finding at step 4.</action>
             </substep>
           </step>

           <step n="4" title="Apply Severity Ladder">
             <substep n="4a" title="Classify Each Finding by Severity">
               <action>Classify into Critical/High/Medium/Low using
                       the HIGHEST applicable severity.</action>
             </substep>
             <substep n="4b" title="Form Each Finding per Rules">
               <action>Cite file:section evidence. Write concrete fix
                       recommendation. One severity per finding.</action>
             </substep>
           </step>

           <step n="5" title="Emit Finding Report">
             <check if="findings produced">
               <output-format>
                 ## Ticket Review Report

                 **Ticket**: {basename}
                 **Primary tag**: {tag}
                 **Reviewed**: {ISO 8601 UTC}
                 **Total findings**: {N} ({C} Critical, {H} High, {M} Medium, {L} Low)

                 ### Critical (N)
                 (for each Critical finding: location, finding, fix)

                 ### Verdict
                 BLOCK | CONDITIONAL | PASS
               </output-format>
             </check>
           </step>
         </workflow>

       ==========================================================
       PATTERN B — Single-capability with parameter branching
       ==========================================================
       Use when the subagent does one CONCEPTUAL task but its execution
       branches on an input parameter (e.g., codesmith-validator's gate
       parameter selects which angles to run). Use <check if=""> blocks
       inside steps to branch.

         <workflow>
           <step n="1" title="Determine Gate">
             <action>Read gate field from dispatch prompt. Valid values:
                     D-review, P-review, I-per-slice, final-integration.</action>
           </step>
           
           <step n="2" title="Run Gate-Specific Angles">
             <check if="gate == 'D-review'">
               <action>Run angles: architecture, sizing</action>
             </check>
             <check if="gate == 'I-per-slice'">
               <action>Run angles: plan-adherence, code-quality, test-quality</action>
             </check>
             <check if="gate == 'final-integration'">
               <action>Run all mandatory angles plus any conditional angles
                       triggered by I-phase signals.</action>
             </check>
           </step>
           
           <step n="3" title="Emit JSON Findings">
             <output-format>
               {strict JSON schema — see severity-ladder reference}
             </output-format>
           </step>
         </workflow>

       ==========================================================
       MULTI-CAPABILITY? USE A DUAL-MODE PRIMARY, NOT A SUBAGENT
       ==========================================================
       If you are reaching for a subagent that hosts MULTIPLE
       capabilities — different skills selected per dispatch — stop. That
       is a dual-mode primary, not a subagent. A primary carries a menu of
       capabilities: in INTERACTIVE mode a human selects one; in
       AUTONOMOUS mode (dispatched via Task) the agent infers which menu
       item the request maps to and runs it. The runtime strips the
       question tool when a primary is dispatched, so one agent serves
       both callers.

       The researcher agent is the canonical example: one persona, a menu
       of research capabilities (quick-answer, focused-study, investigate,
       compare, precedent, scout-extern, risk), each backed by its own
       skill. Build it via the primary agent path (frontmatter + persona +
       menu), NOT this subagent-instructions template.

       Subagents are SINGLE-capability: one focused task, structured
       input, structured return. Use Pattern A or Pattern B.

        ==========================================================
        PICKING THE RIGHT PATTERN
        ==========================================================
        Multi-capability (multiple skills selected per dispatch) → not a
        subagent at all; build a dual-mode primary with a menu (see above).

        Single-capability (Patterns A or B) when:
          - One focused purpose
          - Priors-activation IS the workflow context

        Pattern B specifically when:
          - Single conceptual task BUT execution branches on a parameter
          - The branches are small enough to inline (5-10 lines each)
          - The branches share the same output shape

        Otherwise Pattern A (embedded single-capability workflow).

        ==========================================================
        OUTPUT FORMAT PLACEMENT
        ==========================================================
        The output format ALWAYS lives inside the <workflow> tag, never
        as a separate top-level tag. Concretely:
          - Pattern A/B: <output-format> as the last step's content, OR
            as a sibling tag at the end of <workflow>

       Rationale: output is part of HOW the subagent executes
       (workflow). Splitting it into a separate top-level tag creates
       a phantom 3rd section that's actually just the final step's
       deliverable.

       ==========================================================
       PHASED STEPS WITH SUBSTEPS
       ==========================================================
       When a workflow step has distinct conceptual phases (e.g., run
       commands → classify results → route on outcome), decompose it
       into named <substep n="Xa" title="..."> blocks. This gives each
       phase its own addressable slot for todo tracking, makes the
       structure scannable, and matches the engine's own substep
       vocabulary (see shared/workflow-engine.md).

       When to use substeps:
         - Step has 2+ distinct conceptual phases
         - Phases share output state but represent separable work
         - Iteration cycles (e.g., red-green-refactor in TDD execution)
         - Classification + routing patterns (run → classify → branch)

       When to skip substeps:
         - Step is atomic (single action, single output)
         - Phases are tightly sequenced micro-actions that read as one
           thought ("stage, commit, push" is borderline — substeps
           clarify; flat <action> is also acceptable)

       Substep naming: lowercase letter suffix on the parent step
       number (1a, 1b, 1c). Match the engine's internal convention.

         <step n="2" title="Run Verification Commands">
           <substep n="2a" title="Run Each Verification Command">
             <action>Run each command in {{verification_commands}}.
                     Capture results.</action>
           </substep>

           <substep n="2b" title="Classify Failures and Route">
             <check if="all commands pass">
               <action>Proceed to step 3.</action>
             </check>
             <check if="failure is fixable in slice scope">
               <action>Fix; re-run 2a.</action>
             </check>
             <check if="slice too large">
               <action>Jump to step N and emit NEEDS_DECOMPOSITION.</action>
             </check>
           </substep>
         </step>

       Substeps can carry optional="true" and reuse the same execution
       tags (<action>, <check if="">, <ask>, <invoke-agent>) as steps.

       ==========================================================
       RETURN-SIGNAL MULTIPLICITY
       ==========================================================
       Subagents commonly need to emit different output shapes for
       different runtime conditions. Express each return signal as its
       own <check if=""> block inside the final step, with the
       <output-format> nested inside the matching condition.

       Common signal classes:
         - ERROR — dispatch context is missing/malformed (orchestrator
           bug); no work performed. ALWAYS the first-step output.
         - CLARIFICATION_NEEDED — recoverable ambiguity; the subagent
           needs more context to proceed but the dispatch was otherwise
           well-formed. Dispatching caller can re-dispatch to the same
           Task session via session resume with the answer. The
           subagent's state persists between dispatches.
         - Success signal — work completed; structured payload (e.g.,
           PHASE_COMPLETE with commit SHA, finding report with verdict)
         - Domain-specific signals — runtime conditions the orchestrator
           must route on (e.g., NEEDS_DECOMPOSITION when scope was too
           large; PLAN_DRIFT when assumptions don't match reality)
         - External-signal handling — STOP signals from monitoring
           plugins; abort conditions

       Distinguish three categories by recipient semantics:
         - ERROR — orchestrator's fault; orchestrator must fix dispatch
           before re-trying
         - CLARIFICATION_NEEDED — neither party's fault; orchestrator
           supplies the missing context and re-dispatches
         - Domain signals — runtime condition; orchestrator decides next
           action based on the signal's payload

         <step n="1" title="Validate Dispatch">
           <action>
             Verify all required inputs present and well-formed. If
             missing or malformed, emit:

               ERROR: Missing or malformed dispatch field '{field}'.
               The dispatching orchestrator failed to supply complete
               dispatch context. No work performed.

             And stop.
           </action>
         </step>

         ... intermediate steps ...

         <step n="N" title="Emit Return Signal">
           <check if="work completed successfully">
             <output-format>
               SUCCESS_SIGNAL
               {structured payload}
             </output-format>
           </check>

           <check if="clarification needed to proceed">
             <output-format>
               CLARIFICATION_NEEDED
               {one-sentence description of what's missing and why}
             </output-format>
           </check>

           <check if="domain condition X — needs orchestrator routing">
             <output-format>
               DOMAIN_SIGNAL_X
               {context the orchestrator needs to route correctly}
             </output-format>
           </check>

           <check if="external STOP signal received">
             <action>
               Discard in-progress work. Emit DOMAIN_SIGNAL_X with
               completed-so-far payload.
             </action>
           </check>
         </step>

       Each signal MUST include enough context for the orchestrator to
       route correctly without re-running the subagent. ERROR names the
       field; CLARIFICATION_NEEDED names the missing context and why;
       success signals carry payloads; domain signals carry the
       condition + the orchestrator-relevant context (what was
       completed, what's blocked, what's affected downstream).

       ==========================================================
       CAPABILITY BOUNDARIES — WHAT GOES WHERE
       ==========================================================
       This template does NOT have a <scope> tag. Capability boundaries
       live in three places, by KIND:

         Hard prohibitions (can the subagent edit files? run bash?
         spawn subagents?):
           → frontmatter.md permission map
           → runtime-enforced; no need to state in prose

         Affirmative stance (what the subagent FOCUSES on; what's the
         orchestrator's job):
           → persona.md <principles>
           → priors activation; positive framing
           → e.g., "Review for durability; orchestrator applies fixes"

         Operational discipline (what each step does; what NOT to do
         within a step):
           → workflow's <step> and <action> content
           → step-local; tied to the specific action
           → e.g., "Synthesize, do not paste raw subagent output"

       When tempted to add a <scope> tag with "do not X" prose, ask:
         - Is X enforced by permissions? → frontmatter map
         - Is X about overall focus? → persona principles
         - Is X about a specific step? → workflow step content
       
       If none of the three fit, the redirection is probably too vague
       to be useful — sharpen it until it fits one home.
  -->
</workflow>
