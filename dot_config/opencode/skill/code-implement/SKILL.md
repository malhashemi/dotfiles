---
name: code-implement
description: "I-phase orchestration skill per Lock 10. Iterates over the locked plan's slices in dependency order. For each slice: invokes worktree-setup (first slice only or once per parallel plan); dispatches `codesmith-worker` subagent with slice scope (plan + slice boundary + verification commands + commit convention + worktree path); awaits PHASE_COMPLETE or NEEDS_DECOMPOSITION; on decomposition triggers mini-replan per Lock 19; on completion invokes `code-verify` for the I-per-slice gate. Owns the plan-as-living-doc's structural sections; worker owns the per-slice log subsections. Tracks decomposition strike count (abort after 3 consecutive on the same slice per Lock 17.2)."
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
<skill id="code-implement" name="Code Implement" version="1.0">

  <overview>
    <purpose>
      Orchestrate I-phase: dispatch codesmith-worker subagents
      slice-by-slice in the worktree; handle decomposition; gate each
      slice through code-verify's I-per-slice gate.
    </purpose>

    <inputs>
      Session state (execution mode, post-compact per Lock 20):
      - bundle_dir, ticket_path, ticket_alias, ticket_slug, primary_tag
      - design_path (locked), structure_path (locked)
      - plan_paths (locked), plan_count
      - parallel_safety (parallel | sequential | N/A)
      - pr_mode
    </inputs>

    <outputs>
      All slices implemented, committed, V-passed.
      Plan doc(s) updated with implementation log subsections per
      slice (kept lean via three-condition gate).

      Final handoff routes to:
      - PR mode → pr-cycle (then human merge → wt remove)
      - Local mode → local-merge (then ticket → verified)
    </outputs>

    <orchestrator-discipline critical="true">
      NEVER implement slices yourself. ALWAYS spawn codesmith-worker
      via Task tool. Your job is dispatch, gate-handling, and plan
      ownership — not coding.

      Plan-as-living-doc ownership (Lock 10):
      - YOU own: structural plan changes (add/remove/reorder slices),
        frontmatter, scope changes, high-level approach when drift is
        significant
      - WORKER owns: checkbox marks ([ ] → [x]), per-slice
        implementation log subsections, deviation records

      Parallel slices write to separate per-slice subsections (low
      conflict probability per Lock 9 parallel-work isolation rule).

      Mini-Q-R per slice (Lock 10): worker is enabled with Task tool
      to dispatch researcher for codebase-freshness checks before
      writing slice code. Worker does NOT receive design/structure/
      research docs — only the plan + slice boundary + verification
      commands.
    </orchestrator-discipline>
  </overview>

  <workflow>

    <step n="1" title="Determine Execution Mode">
      <action>Load and execute: references/steps/step-01-determine-mode.xml</action>
    </step>

    <step n="2" title="Setup Worktree(s)">
      <action>Load and execute: references/steps/step-02-setup-worktrees.xml</action>
    </step>

    <step n="3" title="Dispatch Worker for Next Slice">
      <action>Load and execute: references/steps/step-03-dispatch-worker.xml</action>
    </step>

    <step n="4" title="Handle Worker Return">
      <action>Load and execute: references/steps/step-04-handle-worker-return.xml</action>
    </step>

    <step n="5" title="I-per-slice Verification Gate">
      <action>Load and execute: references/steps/step-05-verify-slice.xml</action>
    </step>

    <step n="6" title="Loop or Complete">
      <action>Load and execute: references/steps/step-06-loop-or-complete.xml</action>
    </step>

    <step n="7" title="Final Integration + Handoff">
      <action>Load and execute: references/steps/step-07-final-integration.xml</action>
    </step>

  </workflow>

  <completion>
    <action>
      All slices verified. Workflow hands off to either pr-cycle (PR
      mode) or local-merge (local-only mode) for the V-phase merge
      stage. After merge, the calling primary agent transitions the
      ticket to `verified` via transition-ticket-status.py.
    </action>
  </completion>

</skill>
