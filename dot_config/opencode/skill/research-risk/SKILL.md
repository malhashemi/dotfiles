---
name: research-risk
description: "Identify what could go wrong with a proposed approach before it bites — an adversarial reconnaissance across the risk categories that apply (security, performance, regulatory, operational, correctness, cost). Selects the relevant risk lenses for the approach, scans each against the approach's own description, our internal exposure (codebase), prior incidents (thoughts archive), and known external risks (web), then builds a risk register: each risk with an evidence-grounded likelihood and impact, and the standard mitigation for its class. Adversarially skeptical — an approach that looks clean still gets its residual and low risks surfaced rather than declared all-clear. States risks and their known mitigations factually; whether and how to remediate is the orchestrator's call. Persists the register as a planning input. Mode-aware. The right capability for 'what could go wrong with this rollout?', 'security risks of this auth design', 'where does this approach break under load?'."
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
<skill id="research-risk" name="Research Risk" version="1.0">

  <overview>
    <purpose>
      Identify what could go wrong with a proposed approach. Select the
      risk categories that apply, scan each adversarially across the
      approach, our internal exposure, prior incidents, and known
      external risks, and build a risk register with evidence-grounded
      likelihood, impact, and standard mitigations.
    </purpose>

    <inputs>
      Interactive (user invokes [RX]):
      - The approach to assess (a plan, design, code path, or described
        approach); mentioned sources read first.

      Autonomous (dispatched from a workflow):
      - approach (required): what to assess for risk
      - categories (optional): risk lenses to apply; derived from the
        approach when absent
      - scope (optional): where the approach lives (globs, paths, domain)
      - web_search_approved (boolean): required true to research known
        external risks via web-search-researcher
      - output_location (optional): override for the research directory
    </inputs>

    <outputs>
      A risk register persisted to the thoughts research directory: risks
      grouped by category, each with an evidence-grounded likelihood and
      impact, the standard mitigation for its class, and a citation; a
      Summary ranking the top risks. Autonomous mode returns a structured
      signal carrying the register path.
    </outputs>

    <key-discipline>
      Adversarial stance: the job is to find what breaks. A pre-mortem
      framing — "assume this failed in production; what were the causes?"
      — drives the scan. An approach that looks clean still gets its
      residual and low risks surfaced; "no risks" from an adversarial
      scan is suspicious, not reassuring.

      Mitigations are factual, not directives. State the standard
      mitigation for each risk class ("this is mitigated by X") — never a
      remediation order for our code ("rewrite Z"). Whether, when, and how
      to remediate is the orchestrator's call.

      Likelihood and impact are evidence-grounded. "Likelihood HIGH
      because the input is user-controlled and reaches the query
      unescaped [cite]" — a grading backed by evidence, not a hunch.

      Hide-the-intent: every child prompt carries the risk question
      alone — never the parent task's intent.
    </key-discipline>
  </overview>

  <workflow>

    <step n="1" title="Orient">
      <action>Load and execute: references/steps/step-01-orient.xml</action>
    </step>

    <step n="2" title="Select Risk Categories">
      <action>Load and execute: references/steps/step-02-select-categories.xml</action>
    </step>

    <step n="3" title="Dispatch Category Scans">
      <action>Load and execute: references/steps/step-03-dispatch-scans.xml</action>
    </step>

    <step n="4" title="Build Risk Register">
      <action>Load and execute: references/steps/step-04-build-register.xml</action>
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
      After step 6, the register is persisted and the caller has the
      path. In interactive mode, offer to deepen a top risk (Focused
      Study) or compare mitigation approaches (Comparative Matrix).
    </action>
  </completion>

</skill>
