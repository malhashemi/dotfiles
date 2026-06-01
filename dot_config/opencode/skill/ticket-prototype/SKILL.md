---
name: ticket-prototype
description: "Owns the prototyping sub-activity of Q↔R per QRDSPIV. Invoked from ticket-grill (and any future grill-adopting agent) when the gap being explored requires running throwaway code to answer it. Two branches: LOGIC (terminal/minimal runnable for state or business-logic questions) and UI (visual variants for layout/flow/interaction; uses the project's design system if one exists). Prototype code lives at {shared_folder}/tickets/{slug}/prototypes/{name}/; findings are returned to the caller for inclusion in the bundle's research file. Per QRDSPIV: throwaway from day one, one command to run, no persistence by default, skip polish, surface state."
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
<skill id="ticket-prototype" name="Ticket Prototype" version="1.0">

  <overview>
    <purpose>
      Run a throwaway prototype to answer a Q↔R question that codebase research,
      thoughts/ research, or web research cannot answer. Two branches: LOGIC
      for state/business-logic questions; UI for layout/flow/interaction
      questions. Produces a tangible artifact (runnable code in a
      `prototypes/{name}/` directory) and structured findings returned to
      the caller.
    </purpose>

    <output>
      A prototype directory at {shared_folder}/tickets/{slug}/prototypes/{name}/
      containing minimal throwaway code. A findings block returned to the
      caller (ticket-grill) containing:
      - The question the prototype was answering
      - What was built (one-line summary)
      - How it was run (one command)
      - What was learned (factual findings, no opinions)
      - Path to the preserved prototype (for reference if needed later)

      The caller writes these findings into its bundle's research file.
      No separate prototype-findings document is created.
    </output>

    <key-responsibility>
      Prototyping is DISCOVERY, not DELIVERY. The agent must:
      - Resist over-engineering — prototypes are throwaway from day one
      - Resist documentation drift — findings go to the caller's research file, not a separate doc
      - Surface state aggressively — log/print/render intermediate state so the question gets answered
      - For UI: check for a design system and use it; ad-hoc styling produces misleading evidence about what the real product would look like
      - For LOGIC: keep it terminal — single-file scripts beat multi-file projects for a throwaway

      Per QRDSPIV: "Throwaway from day one, one command to run, no
      persistence by default, skip polish, surface state, delete or absorb
      findings when done. The answer extracted from a prototype belongs in
      the parent artifact (Brief, Spec, ADR); the prototype itself is
      evidence."
    </key-responsibility>
  </overview>

  <workflow>

    <step n="1" title="Receive Question and Choose Branch">
      <action>Load and execute: references/steps/step-01-choose-branch.xml</action>
      <note>
        Read the question from the caller's context. Decide LOGIC vs UI
        based on the question's shape. Get user confirmation if the choice
        is ambiguous.
      </note>
    </step>

    <step n="2" title="Prepare Prototype Location">
      <action>Load and execute: references/steps/step-02-prepare-location.xml</action>
      <note>
        Resolve the bundle directory from the caller's context. Create
        {shared_folder}/tickets/{slug}/prototypes/{name}/. For UI:
        detect the project's design system (if any) and load its conventions.
      </note>
    </step>

    <step n="3" title="Scaffold Throwaway Files">
      <action>Load and execute: references/steps/step-03-scaffold-files.xml</action>
      <note>
        Create the minimal runnable. LOGIC: a single file (Python, TypeScript,
        shell — whatever fits the language ambient in the codebase). UI: an
        index.html plus minimal CSS/JS, design-system-aware. One-command
        runnable; no build step if avoidable; surface state aggressively.
      </note>
    </step>

    <step n="4" title="Run and Observe">
      <action>Load and execute: references/steps/step-04-run-and-observe.xml</action>
      <note>
        Execute the prototype OR present it to the user (UI prototypes
        usually require visual review). Capture observations. Iterate on
        the prototype only if the first run did not answer the question;
        cap iterations at 2-3 — beyond that, the question may be too
        complex for prototyping and should escalate to a spike ticket.
      </note>
    </step>

    <step n="5" title="Extract Findings and Return">
      <action>Load and execute: references/steps/step-05-extract-findings.xml</action>
      <note>
        Synthesize what was learned into a structured findings block.
        Return to the caller for inclusion in the bundle's research file.
        Preserve the prototype directory as a reference path. Do NOT write
        the findings to a separate prototype-findings doc.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      After step 5, the caller (ticket-grill) receives:
      - findings_block (markdown ready to append to the research file)
      - prototype_path (the preserved prototype directory)

      The caller writes findings_block into the research file (in its own
      step-05 update-bundle-files); the prototype directory remains as a
      reference. The ticket-prototype skill itself does not write to the
      bundle's research file — that responsibility stays with the caller.
    </action>
  </completion>

</skill>
