---
name: ticket-design
description: "D-phase skill for the ticket-writing workflow. Runs brain-surgery alignment with the user on the WORK to be done (not the technical solution — at the ticket-writing layer, D designs the work, not the implementation). Loads the Q↔R-ready bundle, drafts a design proposal (artifact chain + decision points + risk), aligns with user via firm checkpoint, handles redirects with the three-strike-foundational-reversal escalation counter from Lock 31, and writes the Design Summary into the ticket body. Hands off to ticket-structure."
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
<skill id="ticket-design" name="Ticket Design" version="1.0">

  <overview>
    <purpose>
      Run the D-phase of the ticket-writing QRDSPIV: brain-surgery
      alignment with the user on the WORK to be done. Per QRDSPIV: "D is a
      conversation, not a document. The agent presents understanding; the
      human validates or redirects." At the ticket-writing layer, D
      designs the WORK (artifact chain, decision points, risk areas) —
      NOT the technical implementation, which belongs to the downstream
      implementation-QRDSPIV's D-phase.
    </purpose>

    <output>
      A Design Summary section written into the ticket body containing:
      - Restated scope (refined further if D-phase surfaces gaps)
      - Artifact chain (which downstream artifacts will need creating or modifying)
      - Decision points (where future user touchpoints sit)
      - Risk areas (where the work is most likely to surface friction)

      If the user's redirects during D-phase reach three foundational
      reversals (per Lock 31), the skill recommends abort and offers to
      archive the bundle as research evidence for a fresh Q↔R session.

      Bundle state after this skill: ready for ticket-structure.
    </output>

    <key-responsibility>
      D is the alignment-or-loopback phase. Three outcomes are possible:

      1. **User confirms the design** → proceed to ticket-structure. This
         is the green-path outcome.

      2. **User redirects scope** → loop back to ticket-grill if the
         redirect reveals an un-grilled scoping gap. The redirect is
         logged in the Q&A file. Strike counter does NOT increment if
         the redirect is a NEW scope concern not previously locked.

      3. **User reverses a foundational decision** (one previously
         confirmed in Q↔R or in an earlier D-phase pass): strike counter
         increments. Three-strike escalation:
         - Strike 1: absorb, loop back to relevant phase, log reversal
         - Strike 2: surface concern — "bundle is becoming inconsistent;
           continue absorbing, or pause to consolidate?"
         - Strike 3: recommend abort — "three foundational reversals
           indicate original scoping was wrong; archive current bundle
           as research evidence, start fresh Q↔R?"

      Strike counter lives in session state; resets per session. The
      user can always insist on continuing past strike 3.
    </key-responsibility>
  </overview>

  <workflow>

    <step n="1" title="Load Bundle and Initialize Strike Counter">
      <action>Load and execute: references/steps/step-01-load-bundle.xml</action>
      <note>
        Read the ticket (especially the Readiness Summary section written
        by ticket-grill), research file, questions file, and linked DRs.
        Initialize the session-scope foundational-strike counter to 0.
      </note>
    </step>

    <step n="2" title="Draft Design Proposal">
      <action>Load and execute: references/steps/step-02-draft-proposal.xml</action>
      <note>
        Compose the design proposal: artifact chain (what downstream
        artifacts will be touched), decision points (where future user
        touchpoints sit), risk areas (where friction is likely). The
        primary tag selects depth via the tag recipe (loaded from
        shared references when those exist; see Phase 4).
      </note>
    </step>

    <step n="3" title="Present and Align" critical="true">
      <action>Load and execute: references/steps/step-03-present-and-align.xml</action>
      <note>
        FIRM CHECKPOINT. Present the proposal to the user as a
        brain-surgery conversation: "Here is the journey this work
        requires; here are the decision points; here is where the risk
        lives. Does this look right?" User confirms, redirects, or
        rejects. Strike counter logic happens in step 4 — step 3 is
        just the presentation and capture of the user's response.
      </note>
    </step>

    <step n="4" title="Handle Redirects and Strike Escalation">
      <action>Load and execute: references/steps/step-04-handle-redirects.xml</action>
      <note>
        Classify the user's response. If confirm → goto step 5. If
        redirect-scope (un-grilled gap) → loop back to ticket-grill via
        explicit recommendation. If foundational reversal → increment
        strike counter and apply the strike-N protocol. If abort →
        archive the bundle and exit cleanly.
      </note>
    </step>

    <step n="5" title="Finalize and Handoff">
      <action>Load and execute: references/steps/step-05-finalize-and-handoff.xml</action>
      <note>
        Write the locked Design Summary into the ticket body. Stamp
        last_updated. Re-validate. Recommend ticket-structure as the
        next step via the ticketsmith menu.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      After step 5 completes, the ticket file has a Design Summary
      section, the user has confirmed the work shape, and the bundle is
      ready for ticket-structure.

      Present the user with:
      1. The Design Summary that was written
      2. Bundle file paths (ticket, research, questions, any DRs)
      3. Strike counter status (if non-zero, note that prior reversals
         occurred this session)
      4. Next action: invoke `ticket-structure` from the ticketsmith
         menu (cmd: TS) to define the ticket's section/Parts shape.
    </action>
  </completion>

</skill>
