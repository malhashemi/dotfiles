---
name: ticket-write
description: "I-phase skill for the ticket-writing workflow. Drafts the ticket section-by-section per the Writing Plan from ticket-plan. Pre-dispatches all planned subagents in parallel before writing begins (efficiency win); iterates through sections in writing order; pauses at planned checkpoints for user review. Each section follows AGENT-BRIEF discipline: durability over precision (no file paths, no line numbers); behavioral, not procedural; complete acceptance criteria; explicit scope boundaries. Hands off to ticket-verify."
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
<skill id="ticket-write" name="Ticket Write" version="1.0">

  <overview>
    <purpose>
      Run the I-phase of the ticket-writing QRDSPIV: actually draft the
      ticket body section-by-section per the Writing Plan from
      ticket-plan. Pre-dispatch all planned subagents in parallel before
      writing begins (efficiency win); iterate through sections in
      writing order; pause at planned checkpoints for user review.
    </purpose>

    <output>
      The ticket body fully drafted with every section from the
      Structure Outline filled per its scope note and the AGENT-BRIEF
      discipline (see references/agent-brief-principles.md). The
      ticket still has status: draft — only ticket-verify transitions
      it to 'ready'.

      Bundle state after this skill: ready for ticket-verify.
    </output>

    <key-responsibility>
      Every section drafted by this skill must honor AGENT-BRIEF
      discipline (loaded from references/agent-brief-principles.md):

      - Durability over precision: no file paths or line numbers in
        section bodies; durable identifiers (capability names, entity
        names, behavioral descriptors)
      - Behavioral, not procedural: WHAT, not HOW
      - Complete acceptance criteria: every AC is testable
      - Explicit scope boundaries: out-of-scope is as load-bearing as in-scope
      - Self-sufficient: ticket carries all WHAT-and-WHY context
      - Decisions in ticket; tactics in plan
      - Read against the Design Summary

      The Risk Areas section is an exception to the "no file paths"
      rule — evidence citations there are bound to research findings
      and are durable for THAT purpose (they document where the
      research found friction).
    </key-responsibility>
  </overview>

  <workflow>

    <step n="1" title="Load Bundle">
      <action>Load and execute: references/steps/step-01-load-bundle.xml</action>
      <note>
        Read the ticket (all prior phase sections), research, questions,
        linked DRs, and the Writing Plan. Also load
        references/agent-brief-principles.md into working memory — every
        section drafted in step 3 must honor it.
      </note>
    </step>

    <step n="2" title="Pre-Flight Subagent Dispatch">
      <action>Load and execute: references/steps/step-02-preflight-dispatch.xml</action>
      <note>
        Dispatch all subagents flagged in the Writing Plan in parallel
        BEFORE writing begins. Collect their findings into session
        memory keyed by section name. This means step 3 can write
        sections without blocking on per-section dispatch.
      </note>
    </step>

    <step n="3" title="Write Sections (Iterate)">
      <action>Load and execute: references/steps/step-03-write-iterate.xml</action>
      <note>
        For each section in writing order:
        - Draft the section per its scope note, the Design Summary,
          and AGENT-BRIEF principles
        - Apply the section-quality checklist (from
          agent-brief-principles.md)
        - Write to the ticket body via Edit (append; never overwrite
          prior phase sections)
        - If this section is followed by a planned checkpoint, pause
          via Question tool for user review
        - Stamp last_updated after every Part boundary checkpoint
        - Continue until all sections are drafted
      </note>
    </step>

    <step n="4" title="Finalize and Handoff">
      <action>Load and execute: references/steps/step-04-finalize-and-handoff.xml</action>
      <note>
        Stamp last_updated with the final state. Re-validate the bundle.
        Recommend ticket-verify as the next step.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      After step 4, the ticket body is fully drafted but status remains
      'draft'. Present:
      1. The final ticket file path
      2. Total length actual vs estimated (from Writing Plan)
      3. Number of subagent dispatches performed
      4. Number of checkpoints triggered
      5. Next action: invoke `ticket-verify` from the ticketsmith menu
         (cmd: TV) for self-review + reviewer subagent dispatch +
         draft→ready gate.
    </action>
  </completion>

</skill>
