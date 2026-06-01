---
name: ticket-grill
description: "Q↔R loop skill for the ticket-writing workflow. Runs iterative grilling against an oriented ticket bundle until the five readiness criteria from QRDSPIV are met. Mode-shifts between brainstorming, research, elicitation, and prototyping. Dispatches research subagents in parallel per the question-shape→subagent table. Updates CONTEXT.md inline via the context-md-format skill. Writes Decision Records via the decision-record-format skill when the three-condition gate fires. Loops back to itself until ready; hands off to ticket-design when readiness is confirmed."
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
<skill id="ticket-grill" name="Ticket Grill" version="1.0">

  <overview>
    <purpose>
      Run the Q↔R loop on an oriented ticket bundle until the five readiness
      criteria are met (problem scoped, current state mapped, impact
      understood, edge cases identified, agent can articulate understanding
      unprompted). Q↔R is iterative; this skill loops back to itself across
      turns and exits only when readiness is confirmed.
    </purpose>

    <output>
      An updated ticket bundle where:
      - The research file holds factual findings from subagent dispatch
      - The questions file holds every Q↔R exchange (question, chosen answer,
        rejected alternatives with brief why-not)
      - CONTEXT.md (or its per-context variants) reflects any terms resolved
        during grilling
      - Zero or more Decision Records have been scaffolded in
        {shared_folder}/decisions/ for hard-to-reverse decisions that surfaced
      - The ticket file's body has the user-request restatement and (if the
        loop concluded) the readiness summary; the design summary lives in
        ticket-design, not here
      Session state ready for ticket-design.
    </output>

    <key-responsibility>
      Grilling is patient work. The agent stays in this loop until the
      readiness criteria are GENUINELY met, not until impatience overrides
      them. Each turn:
      1. Reads the current bundle state
      2. Orients on what is known vs unknown
      3. Formulates one focused user-facing question OR a research agenda
      4. Dispatches subagents in parallel per the question-shape table
      5. Synthesizes findings, writes them to the research doc, logs the Q&A
      6. Checks readiness; if not ready, loops back to step 2

      The four Q↔R sub-activities (brainstorming, research, elicitation,
      prototyping) are mode-shifts within this loop, not separate phases.
      The "hide the intent" pattern from QRDSPIV applies only to
      implementation Q↔R, NOT here — ticket-writing grilling is open about
      what is being grilled.
    </key-responsibility>
  </overview>

  <workflow>

    <step n="1" title="Load Bundle">
      <action>Load and execute: references/steps/step-01-load-bundle.xml</action>
      <note>
        Read the ticket, research, questions files, the Orient Summary
        breadcrumb from the questions file, and CONTEXT.md. This is the
        only step that runs once per session; all subsequent steps may
        loop multiple times.
      </note>
    </step>

    <step n="2" title="Orient on Current State">
      <action>Load and execute: references/steps/step-02-orient-current-state.xml</action>
      <note>
        Re-assess what is known and what is unknown after the last turn's
        findings (or, on the first turn, after the Orient Summary).
        Identify the highest-value gap to close THIS turn.
      </note>
    </step>

    <step n="3" title="Formulate Questions">
      <action>Load and execute: references/steps/step-03-formulate-questions.xml</action>
      <note>
        Split the turn's questions into:
        - User-directed (asked immediately via Question tool — firm checkpoint)
        - Research agenda (dispatched to subagents in step 4)
        - Artifact checks (e.g., reading specs, briefs, existing thoughts/ docs)
      </note>
    </step>

    <step n="4" title="Dispatch and Synthesize">
      <action>Load and execute: references/steps/step-04-dispatch-and-synthesize.xml</action>
      <note>
        Dispatch 2-4 subagents in parallel per the question-shape table at
        references/subagent-dispatch.md. Wait for ALL to return. Synthesize
        findings into the research file. This step never runs serially —
        parallel is mandatory.
      </note>
    </step>

    <step n="5" title="Update Bundle Files">
      <action>Load and execute: references/steps/step-05-update-bundle-files.xml</action>
      <note>
        Write the turn's Q&A to the questions file (one entry per resolved
        question with the chosen answer + rejected alternatives + brief
        why-not). Update CONTEXT.md inline if any terms were resolved
        (via context-md-format skill). If a hard-to-reverse decision
        surfaced and the three-condition gate fires, scaffold a Decision
        Record (via decision-record-format skill and
        scaffold-decision-record.py). Stamp last_updated on every modified
        bundle file.
      </note>
    </step>

    <step n="6" title="Readiness Gate">
      <action>Load and execute: references/steps/step-06-readiness-gate.xml</action>
      <note>
        Check all five readiness criteria. If any is not yet true, present
        the gap to the user with a Question tool checkpoint and loop back
        to step 2. If all five are true, present the readiness summary
        and hand off to ticket-design.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      When step 6 confirms readiness, the bundle is ready for ticket-design.
      Present the user with:
      1. Readiness summary (one paragraph: what was learned, what was decided)
      2. Bundle file paths (ticket, research, questions, any spawned DRs)
      3. Next action: invoke the `ticket-design` skill from the ticketsmith
         menu (cmd: TD) for the Design phase.
    </action>
  </completion>

</skill>
