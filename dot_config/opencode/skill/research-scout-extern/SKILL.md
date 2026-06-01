---
name: research-scout-extern
description: "Scout an external open-source codebase for patterns and implementations, and persist the findings to a global, cross-project research catalog. Catalog-first: checks what has already been studied before cloning, so a repeat question reuses prior research instead of re-cloning. When a clone is needed, sets up a disposable .extern/ workspace, shallow-clones the repo, studies it with the read-only codebase children (pattern-finder, analyzer, locator) focused on the study topic, writes a research document to the global extern store, and records the study in the catalog via script. Clones are disposable; research is permanent. Studies code, not the web — invoking the skill is the approval to clone. Mode-aware: interactive confirms cleanup of the workspace; autonomous leaves the clone in place. The right capability for 'study how vercel/next.js implements middleware', or as the deep-study follow-up when Precedent Reconnaissance flags an external project worth reading in depth."
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
<skill id="research-scout-extern" name="Research Scout External" version="1.0">

  <overview>
    <purpose>
      Scout an external open-source codebase for patterns and persist the
      findings to a global, cross-project catalog. Catalog-first: reuse
      prior research before cloning. Clones are disposable; research is
      permanent.
    </purpose>

    <inputs>
      Interactive (user invokes [SC]):
      - A repo to study (URL, org/repo, or clone command) and a topic;
        cleanup confirmed at the end.

      Autonomous (dispatched from a workflow, e.g., a Scout follow-up
      recommended by Precedent Reconnaissance):
      - repo (required): URL, org/repo, or clone command
      - topic (required): what to study in the repo
      - context (optional): why — the prompting need, recorded in the catalog
    </inputs>

    <outputs>
      A research document persisted to the global extern store
      (repos/{org-repo}/), the catalog updated via script, and the clone
      either left in .extern/ (autonomous) or cleaned up (interactive,
      confirmed). Autonomous mode returns a structured signal carrying
      the document path and whether prior research was reused.
    </outputs>

    <key-discipline>
      Catalog-first: never clone what has already been studied
      sufficiently. Search the catalog before touching the network; reuse
      or note the gap.

      Disposable clone, permanent research: clones live under .extern/
      (gitignored, deletable); findings persist to the global extern
      store and the catalog. Never store value in .extern/.

      Manage the catalog only through scripts/catalog.py — never
      hand-edit catalog.md.

      Hide-the-intent: every child prompt studying the clone carries the
      study question alone — never the parent task's intent.

      Transfer is factual: "Applicable Patterns" states what matches and
      what differs from our work, not a recommendation to adopt.
    </key-discipline>
  </overview>

  <workflow>

    <step n="1" title="Orient and Catalog Discovery">
      <action>Load and execute: references/steps/step-01-orient-discover.xml</action>
    </step>

    <step n="2" title="Workspace and Clone">
      <action>Load and execute: references/steps/step-02-workspace-clone.xml</action>
    </step>

    <step n="3" title="Study the Clone">
      <action>Load and execute: references/steps/step-03-study.xml</action>
    </step>

    <step n="4" title="Synthesize and Persist">
      <action>Load and execute: references/steps/step-04-synthesize-persist.xml</action>
    </step>

    <step n="5" title="Cleanup and Return">
      <action>Load and execute: references/steps/step-05-cleanup-return.xml</action>
    </step>

  </workflow>

  <completion>
    <action>
      After step 5, the study is persisted to the global catalog and the
      caller has the document path. In interactive mode, offer a related
      study (another topic in the same repo) or a comparison against an
      internal approach.
    </action>
  </completion>

</skill>
