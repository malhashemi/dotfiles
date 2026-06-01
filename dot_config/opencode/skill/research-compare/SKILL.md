---
name: research-compare
description: "Compare two or more alternatives in a structured tradeoff matrix — libraries, technologies, vendors, or approaches. Derives the comparison criteria from the decision context (or accepts caller-supplied criteria), researches each alternative on every criterion in parallel tracks across the hide-the-intent boundary, and builds an evidence-backed matrix where each cell carries a citation. Surfaces per-criterion tradeoffs factually (on X, A leads; on Y, B leads) but does NOT compute weighted scores or declare a winner — which weights matter, and which alternative wins, belongs to the orchestrator. Persists the matrix as a decision-input document. Mode-aware: interactive confirms criteria and reviews the matrix; autonomous returns the matrix path. The right capability for 'Postgres vs Cassandra for our workload', 'Stripe vs Adyen', 'REST vs GraphQL for this API'."
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
<skill id="research-compare" name="Research Compare" version="1.0">

  <overview>
    <purpose>
      Compare alternatives in a structured tradeoff matrix. Derive the
      criteria, research each alternative on every criterion in parallel,
      build an evidence-backed grid, surface per-criterion tradeoffs —
      without declaring a winner. Persist as a decision-input document.
    </purpose>

    <inputs>
      Interactive (user invokes [CM]):
      - Two or more alternatives to compare; criteria proposed and
        confirmed; mentioned sources read first.

      Autonomous (dispatched from a workflow):
      - alternatives (required): array of two or more to compare
      - criteria (optional): comparison dimensions; derived from context
        when absent
      - decision_context (optional): what the comparison informs, used to
        derive criteria
      - web_search_approved (boolean): required true for external
        alternatives researched via web-search-researcher
      - output_location (optional): override for the research directory
    </inputs>

    <outputs>
      A tradeoff matrix persisted to the thoughts research directory:
      alternatives × criteria grid with an evidence-backed, cited cell
      per pairing; per-criterion tradeoff notes; a Summary stating the
      shape of the tradeoff — but no weighted score and no declared
      winner. Autonomous mode returns a structured signal carrying the
      matrix path.
    </outputs>

    <key-discipline>
      No winner. A comparison matrix tempts toward "and the best is" —
      that is a recommendation, and which alternative wins depends on
      weights the orchestrator owns. State per-criterion tradeoffs
      factually and the overall shape of the tradeoff; do NOT compute a
      weighted total or declare a choice.

      Evidence per cell. Every cell carries a citation. An uncited cell
      is an impression, not a comparison. "Could not determine" is a
      valid, honest cell.

      Hide-the-intent: every child prompt carries the alternative + the
      criteria to assess — never the parent task's intent or which
      alternative is hoped to win.
    </key-discipline>
  </overview>

  <workflow>

    <step n="1" title="Orient">
      <action>Load and execute: references/steps/step-01-orient.xml</action>
    </step>

    <step n="2" title="Derive Criteria">
      <action>Load and execute: references/steps/step-02-derive-criteria.xml</action>
    </step>

    <step n="3" title="Dispatch per-Alternative Research">
      <action>Load and execute: references/steps/step-03-dispatch-research.xml</action>
    </step>

    <step n="4" title="Build Matrix">
      <action>Load and execute: references/steps/step-04-build-matrix.xml</action>
    </step>

    <step n="5" title="Persist">
      <action>Load and execute: references/steps/step-05-persist.xml</action>
    </step>

    <step n="6" title="Return">
      <action>Load and execute: references/steps/step-06-return.xml</action>
    </step>

  </workflow>

  <completion>
    <action>
      After step 6, the matrix is persisted and the caller has the path.
      In interactive mode, offer to deepen the research on a specific
      alternative (Focused Study) or investigate the decision more
      broadly (Comprehensive Investigation).
    </action>
  </completion>

</skill>
