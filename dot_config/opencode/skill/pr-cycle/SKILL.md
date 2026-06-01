---
name: pr-cycle
description: "Automated PR review cycle for codesmith when PR mode applies. Opens the PR, waits for Gemini Code Assist review via the `await_pr_review` tool, dispatches `codesmith-validator` to assess each unresolved thread against the codebase, implements approved fixes via `codesmith-worker`, responds to threads, requests re-review, and loops until Gemini approves or a context-handoff signal fires. Escalates to human for the final merge decision. NEVER auto-merges. Used at V-phase PR-review gate (Lock 11 gate 5) when PR mode applies; pairs with `local-merge` for the non-PR alternative."
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
<skill id="pr-cycle" name="PR Cycle" version="1.0">

  <overview>
    <purpose>
      Run the PR review cycle for codesmith: open PR → wait for Gemini
      → assess threads → implement fixes → respond → re-review →
      loop until done → escalate to human for merge.
    </purpose>

    <inputs>
      - bundle_dir       Implementation bundle directory
      - ticket_slug      Parent ticket slug
      - ticket_alias     Parent ticket canonical alias
      - branch           Implementation branch (from worktree-setup)
      - target_branch    Target to merge into
      - worktree_path    Worktree path
    </inputs>

    <outputs>
      Returns to caller (JSON):
      {
        "status": "READY_FOR_MERGE" | "CONTEXT_HANDOFF" | "TIMEOUT" | "ERROR",
        "pr_number": <n>,
        "pr_url": "https://...",
        "iterations": <n>,
        "threads_addressed": <n>,
        "threads_declined": <n>,
        "threads_deferred": <n>,
        "commits_added": <n>
      }
    </outputs>

    <hard-constraints>
      NEVER merge the PR. The final merge is always a human decision.
      Violation breaks the trust model.

      NEVER skip the `await_pr_review` tool. Polling Gemini state via
      `gh pr view` directly is forbidden — the tool handles settling
      windows and timeouts.

      NEVER trust Gemini blindly. Every thread requires independent
      verification via `codesmith-validator` before action.

      All threads must be either Addressed (with a commit SHA) +
      resolved, Declined + resolved, or Deferred (with a tracking
      issue) + resolved. No unresolved threads at exit.
    </hard-constraints>
  </overview>

  <workflow>

    <step n="1" title="Initialize PR Cycle State">
      <action>Load and execute: references/steps/step-01-initialize.xml</action>
    </step>

    <step n="2" title="Open PR (first iteration only)">
      <action>Load and execute: references/steps/step-02-open-pr.xml</action>
    </step>

    <step n="3" title="Wait for Gemini Review">
      <action>Load and execute: references/steps/step-03-wait-for-gemini.xml</action>
    </step>

    <step n="4" title="Assess Unresolved Threads">
      <action>Load and execute: references/steps/step-04-assess-threads.xml</action>
    </step>

    <step n="5" title="Validate Assessment">
      <action>Load and execute: references/steps/step-05-validate-assessment.xml</action>
    </step>

    <step n="6" title="Implement Approved Fixes">
      <action>Load and execute: references/steps/step-06-implement-fixes.xml</action>
    </step>

    <step n="7" title="Respond and Resolve Threads">
      <action>Load and execute: references/steps/step-07-respond-threads.xml</action>
    </step>

    <step n="8" title="Request Re-Review and Loop">
      <action>Load and execute: references/steps/step-08-request-re-review.xml</action>
      <action>Increment iteration count; update state file.</action>
      <action>If context warning received: exit with CONTEXT_HANDOFF.</action>
      <action>Else: goto step 3 (wait for Gemini's response to the re-review request).</action>
    </step>

    <step n="9" title="Escalate to Human for Merge">
      <action>Load and execute: references/steps/step-09-escalate-merge.xml</action>
    </step>

  </workflow>

  <completion>
    <action>
      On successful path: PR is approved by Gemini, human has been
      shown the assessment summary, human makes the merge decision
      (not this skill). After merge, the caller (code-verify) runs
      `wt remove` to clean up the worktree, then transitions the
      ticket to `verified`.

      On context-handoff path: state is persisted at
      {bundle_dir}/pr-cycle-state.md; a fresh pr-cycle instance can
      resume from the after-timestamp captured in state.
    </action>
  </completion>

</skill>
