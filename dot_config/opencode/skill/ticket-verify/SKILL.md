---
name: ticket-verify
description: "V-phase skill for the ticket-writing workflow. Self-reviews the drafted ticket against the severity ladder (Critical/High/Medium/Low); dispatches the ticket-reviewer subagent for fresh-context review on feature/exploration/infrastructure tags (no dispatch for bug/hotfix/chore). Resolves findings inline — self-evident fixes apply directly, ambiguous fixes go through user approval per finding, structural findings loop back to an earlier phase. After approved fixes, surfaces the draft→ready gate as the final user checkpoint."
---

<workflow-engine id="vera-workflow-engine-v2.0" name="Execute Workflow">
  <objective>Execute workflow by following instructions and producing output</objective>

  <llm critical="true">
    <mandate>Always read COMPLETE files - NEVER use offset/limit when reading any workflow related files</mandate>
    <mandate>Instructions are MANDATORY - either as file path, steps or embedded list in YAML, XML or markdown</mandate>
    <mandate>Execute ALL steps in instructions IN EXACT ORDER</mandate>
    <mandate>Save to template output file after EVERY "template-output" tag</mandate>
    <mandate>NEVER skip a step - YOU are responsible for every step's execution without fail or excuse</mandate>
  </llm>

  <WORKFLOW-RULES critical="true">
    <rule n="1">Steps execute in exact numerical order (1, 2, 3...) unless an explicit goto directs otherwise</rule>
    <rule n="2">Optional steps: Ask user unless YOLO mode active</rule>
    <rule n="3">Template-output tags: Save content, discuss with the user the section completed, and NEVER proceed until the user indicates to proceed (unless YOLO mode has been activated)</rule>
  </WORKFLOW-RULES>

  <flow>
    <step n="1" title="Process Each Instruction Step in Order">
      <iterate>For each step in instructions:</iterate>

      <substep n="1a" title="Track Progress">
        <action if="first iteration">Create todo list from all instruction step titles (TodoWrite)</action>
        <action>Mark current step as in_progress (TodoWrite)</action>
      </substep>

      <substep n="1b" title="Handle Step Attributes">
        <check>If optional="true" and NOT YOLO -> Use Question tool to ask user whether to include (Yes/Skip)</check>
        <check>If if="condition" -> Evaluate condition</check>
        <check>If for-each="item" -> Repeat step for each item</check>
        <check>If repeat="n" -> Repeat step n times</check>
      </substep>

      <substep n="1c" title="Execute Step Content">
        <action>Process step instructions (markdown or XML tags)</action>
        <action>Replace {{variables}} with values (ask user if unknown)</action>
        <execute-tags>
          <tag>action -> Perform the action</tag>
          <tag>action type="script" -> Execute as shell command, capture output</tag>
          <tag>check if="condition" -> Conditional block wrapping actions (requires closing &lt;/check&gt;)</tag>
          <tag>ask -> Prompt user using Question tool and WAIT for response. When options exist, present them as selectable choices. For open-ended questions, provide helpful suggested options with custom input enabled</tag>
          <tag>invoke-skill name="skill-name" -> Execute another skill via OpenCode skill system</tag>
          <tag>invoke-agent name="subagent" prompt="task" -> Delegate to subagent via Task tool</tag>
          <tag>goto step="x" -> Jump to specified step (used for explicit loop-back in Q-R style flows)</tag>
        </execute-tags>
      </substep>

      <substep n="1d" title="Handle template-output Tags">
        <if tag="template-output">
          <mandate>Generate content for this section</mandate>
          <mandate>Save to file (Write first time, Edit subsequent)</mandate>
          <action>Display generated content</action>
          <action>Use Question tool to present checkpoint options. WAIT for response.
            <options>
              <option label="Continue" description="Approve this section and move to the next step" />
              <option label="Advanced Elicitation" description="Explore this section deeper before proceeding" />
              <option label="YOLO" description="Auto-complete the rest of this workflow without stopping" />
            </options>
            <if response="Advanced Elicitation">
              <action>Invoke advanced-elicitation skill</action>
            </if>
            <if response="Continue">
              <action>Continue to next step</action>
            </if>
            <if response="YOLO">
              <action>Enter YOLO mode for the rest of the workflow</action>
            </if>
          </action>
        </if>
      </substep>

      <substep n="1e" title="Step Completion">
        <action>Mark current step as completed (TodoWrite)</action>
        <check>If no special tags and NOT YOLO:</check>
        <action>Use Question tool to ask:
          <options>
            <option label="Continue" description="Proceed to the next step" />
            <option label="Edit" description="Revise this step before moving on" />
          </options>
        </action>
      </substep>
    </step>

    <step n="2" title="Completion">
      <check>Confirm all instruction steps have been executed</check>
      <output>Workflow complete.</output>
    </step>
  </flow>

  <execution-modes>
    <mode name="normal">Full user interaction and confirmation of EVERY step at EVERY template output - NO EXCEPTIONS except YOLO mode</mode>
    <mode name="yolo">Skip all confirmations and elicitation, minimize prompts and try to produce all of the workflow automatically by simulating the remaining discussions with a simulated expert user</mode>
  </execution-modes>

  <supported-tags desc="Instructions can use these tags">
    <structural>
      <tag>step n="X" goal="..." - Define step with number and goal</tag>
      <tag>substep n="Xa" title="..." - Sub-step within a step</tag>
      <tag>phase n="X" - Phase within a substep</tag>
      <tag>optional="true" - Step can be skipped</tag>
      <tag>if="condition" - Conditional execution</tag>
      <tag>for-each="collection" - Iterate over items</tag>
      <tag>repeat="n" - Repeat n times</tag>
    </structural>
    <execution>
      <tag>action - Required action to perform</tag>
      <tag>action type="script" - Execute shell command</tag>
      <tag>action if="condition" - Single conditional action (inline, no closing tag needed)</tag>
      <tag>check if="condition"&gt;...&lt;/check&gt; - Conditional block wrapping multiple items (closing tag required)</tag>
      <tag>ask - Get user input via Question tool (ALWAYS wait for response before continuing). Present defined options as selectable choices. For open-ended questions, offer helpful suggestions with custom input enabled</tag>
      <tag>goto - Jump to another step (explicit loop-back)</tag>
      <tag>invoke-skill - Call another skill</tag>
      <tag>invoke-agent - Delegate to subagent via Task tool</tag>
      <tag>invoke-protocol - Execute a reusable protocol (e.g., discover_inputs)</tag>
    </execution>
    <output>
      <tag>template-output - Save content checkpoint</tag>
      <tag>critical - Cannot be skipped</tag>
      <tag>example - Show example output</tag>
      <tag>note - Informational content</tag>
      <tag>output - Display to user without saving</tag>
    </output>
    <validation>
      <tag>halt-conditions - Define conditions that MUST stop execution</tag>
      <tag>condition - Single halt condition</tag>
      <tag>validation - Pre-condition rules to check</tag>
    </validation>
  </supported-tags>

  <llm final="true">
    <critical-rules>
      - This is the complete workflow execution engine
      - You MUST follow instructions exactly as written
      - This workflow uses INTENT-DRIVEN PLANNING - adapt organically to product type and context
      - YOU ARE FACILITATING A CONVERSATION with a user to produce a final document step by step
      - The whole process is meant to be collaborative - helping the user flesh out their ideas
      - Do not rush or optimize and skip any section
    </critical-rules>
  </llm>
</workflow-engine>

<?xml version="1.0" encoding="UTF-8"?>
<skill id="ticket-verify" name="Ticket Verify" version="1.0">

  <overview>
    <purpose>
      Run the V-phase of the ticket-writing QRDSPIV: self-review the
      drafted ticket against the severity ladder, dispatch the
      ticket-reviewer subagent for fresh-context review on
      feature/exploration/infrastructure tags, resolve findings inline
      (with user approval for ambiguous fixes; loop-backs for
      structural findings), and gate the draft→ready transition with
      a final user checkpoint.
    </purpose>

    <output>
      A verified ticket at status: ready (or status: draft with open
      findings if verification did not pass).

      The questions file accumulates verify findings as a final
      section, capturing what was reviewed, what was found, what was
      resolved, and what was waived. This is the audit trail for
      future ticket-verify re-runs or implementation-QRDSPIV's V-phase.

      Bundle state after this skill: verified and in the backlog
      (status: ready), or in continuation pending fixes.
    </output>

    <key-responsibility>
      Per spec §10, V is a two-stage review:
      - **Self-review (always)**: this skill runs the severity ladder
        against the ticket regardless of tag.
      - **Reviewer subagent (conditional)**: for primary tags feature /
        exploration / infrastructure, dispatch the ticket-reviewer
        subagent (already authored — read-only, fresh-context).
        Skip the subagent for bug / hotfix / chore (lower stakes;
        self-review suffices per the spec).

      Finding resolution per spec §10.2:
      - Self-evident → apply via Edit directly
      - Ambiguous → Question tool per finding for user approval
      - Structural → loop back to earlier phase (no mini-QRDSPIV)

      The draft→ready gate is the final firm checkpoint. User confirms;
      status transitions; ticket enters the backlog. The user can
      always decline transition and leave the ticket in draft for
      further iteration.
    </key-responsibility>
  </overview>

  <workflow>

    <step n="1" title="Load Bundle">
      <action>Load and execute: references/steps/step-01-load-bundle.xml</action>
      <note>
        Read the ticket, research, questions, linked DRs. Also load
        references/severity-ladder.md into working memory — the
        self-review and finding resolution depend on it.
      </note>
    </step>

    <step n="2" title="Self-Review">
      <action>Load and execute: references/steps/step-02-self-review.xml</action>
      <note>
        Apply the severity ladder against the ticket. Walk through
        each ticket section comparing to the ladder's example
        defects. Produce a self-review finding report.
      </note>
    </step>

    <step n="3" title="Dispatch Reviewer Subagent (Conditional)">
      <action>Load and execute: references/steps/step-03-dispatch-reviewer.xml</action>
      <note>
        For primary tags feature / exploration / infrastructure,
        dispatch the ticket-reviewer subagent via Task tool. Wait for
        its finding report. Merge with the self-review findings,
        deduplicating where both audiences flagged the same issue.
      </note>
    </step>

    <step n="4" title="Resolve Findings">
      <action>Load and execute: references/steps/step-04-resolve-findings.xml</action>
      <note>
        Walk through the merged finding list in priority order
        (Critical → High → Medium → Low). For each finding:
        self-evident fix → Edit directly; ambiguous fix → Question
        tool for user approval; structural finding → identify loop-back
        target and exit cleanly (user re-enters earlier phase, then
        re-runs ticket-verify).
      </note>
    </step>

    <step n="5" title="Transition and Handoff" critical="true">
      <action>Load and execute: references/steps/step-05-transition-and-handoff.xml</action>
      <note>
        Final checkpoint. Verdict: BLOCK / CONDITIONAL / PASS.
        On PASS or CONDITIONAL-with-waivers-applied, present the
        draft→ready gate. User confirms; frontmatter status updates;
        last_updated stamped; ticket enters backlog.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      Two terminal states:

      1. **Verified to ready**: ticket is now in the backlog, available
         for implementation-QRDSPIV pickup. Bundle status reflects
         this. Present the user with bundle paths and a closing note.

      2. **Findings unresolved, still draft**: the verify-phase
         surfaced blocking issues the user did not approve resolution
         for. Ticket remains at status: draft. User can re-invoke
         ticket-verify after addressing the open findings (which may
         require looping back to an earlier phase).

      In both cases, the questions file logs the verify session for
      future audit.
    </action>
  </completion>

</skill>
