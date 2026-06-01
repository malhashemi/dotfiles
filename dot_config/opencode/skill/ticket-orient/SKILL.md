---
name: ticket-orient
description: "Entry-point skill for the ticket-writing workflow. Runs the 7-step orient flow from spec §5: collects thoughts metadata, reads CONTEXT.md, performs tier-1 codebase orientation, detects the candidate primary tag from the user request, confirms scope with the user at a firm checkpoint, scaffolds the ticket bundle directory via scaffold-bundle.py, and hands off to ticket-grill for the Q↔R loop. Use as the first phase of every ticket-writing session before any grilling begins."
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
<skill id="ticket-orient" name="Ticket Orient" version="1.0">

  <overview>
    <purpose>
      Open a new ticket-writing session by orienting on the user's request before
      any grilling begins. Execute the 7-step entry-point flow from the ticket-writing
      workflow spec §5, ending with a scaffolded ticket bundle on disk and a clean
      handoff to the ticket-grill skill.
    </purpose>

    <output>
      A ticket bundle directory at {shared_folder}/tickets/{slug}/ containing three
      schema-valid markdown files (ticket, research, questions) with frontmatter
      populated by scaffold-bundle.py. Session state ready for ticket-grill.
    </output>

    <key-responsibility>
      The orient phase is where wrong assumptions get caught cheaply. The firm
      scope checkpoint in step 5 exists so the agent does not grill on a
      misunderstood request. Skipping it risks burning Q↔R turns on the wrong
      problem.

      Tier 1 reads (step 3) are direct codebase reads for orientation only —
      directory tree, top-level configs, a few representative files. Tier 2
      research goes through subagents and belongs to ticket-grill, not here.
    </key-responsibility>
  </overview>

  <workflow>

    <step n="1" title="Gather Session Metadata">
      <action>Load and execute: references/steps/step-01-thoughts-metadata.xml</action>
      <note>
        Run `thoughts metadata` once and parse the YAML. Capture shared_folder,
        owner, date, team, git context. These values flow into the scaffold
        script in step 6 and into every frontmatter field thereafter.
      </note>
    </step>

    <step n="2" title="Read CONTEXT.md">
      <action>Load and execute: references/steps/step-02-read-context-md.xml</action>
      <note>
        Read the project's shared vocabulary glossary if it exists. Lazy-create
        is deferred to ticket-grill — do not create CONTEXT.md here.
      </note>
    </step>

    <step n="3" title="Tier-1 Codebase Orientation">
      <action>Load and execute: references/steps/step-03-tier-1-orient.xml</action>
      <note>
        Light direct reads only — directory tree, top-level configs, a handful
        of representative source files. Purpose: write informed prompts for
        the subagents that ticket-grill will dispatch. Tier 2 deep research
        is forbidden here; defer to subagents.
      </note>
    </step>

    <step n="4" title="Parse Request and Detect Tag">
      <action>Load and execute: references/steps/step-04-parse-request-detect-tag.xml</action>
      <note>
        Read the user's stated request. Select a candidate primary tag from
        feature / bug / exploration / hotfix / infrastructure / chore. The tag
        is a candidate at this point — step 5's checkpoint may reject it.
      </note>
    </step>

    <step n="5" title="Scope Checkpoint" critical="true">
      <action>Load and execute: references/steps/step-05-scope-checkpoint.xml</action>
      <note>
        FIRM CHECKPOINT. Present back the agent's understanding of the request
        plus the candidate primary tag. User confirms, redirects, or rejects.
        No autonomous proceed. This step is critical="true" — cannot be skipped
        even in YOLO mode. Misunderstood scope at this gate becomes
        misdirected Q↔R for the rest of the session.
      </note>
    </step>

    <step n="6" title="Scaffold Ticket Bundle">
      <action>Load and execute: references/steps/step-06-scaffold-bundle.xml</action>
      <note>
        Invoke scaffold-bundle.py with the confirmed slug, topic, and primary
        tag. The script creates the bundle directory and three schema-valid
        files. Verify the output paths before proceeding.
      </note>
    </step>

    <step n="7" title="Handoff to ticket-grill">
      <action>Load and execute: references/steps/step-07-handoff-to-grill.xml</action>
      <note>
        Final step. Summarize the orient outcome (bundle paths, primary tag,
        scope statement, CONTEXT.md status, key tier-1 findings). Transition
        the session into the Q↔R phase by recommending the ticket-grill skill
        to the user via the agent's menu.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      After step 7 completes, the bundle exists on disk, the user has confirmed
      scope, and the candidate primary tag is locked. Present the user with:
      1. The bundle directory path
      2. The three file paths (ticket, research, questions) with kind: questions
         confirmed on the third file per Lock 37
      3. Next action: invoke ticket-grill from the ticketsmith menu (cmd: TG)
    </action>
  </completion>

</skill>
