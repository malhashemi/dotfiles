---
name: skill-creator
description: "Guides creation of dubstack skill source files (skill.yaml + head.md + skill-overview.md + step files) through discovery, type selection, and section-by-section configuration. Two critical decisions shape every skill: TYPE (workflow / exec / data) and SCRIPTS (script-first mentality — if anything CAN be a script, it probably SHOULD be). Used when creating a new skill for an agent in dubstack."
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
<skill id="skill-creator" name="Skill Creator" version="1.0">

  <overview>
    <purpose>
      Guide the creation of a new dubstack skill source file set
      (skill.yaml + head.md + skill-overview.md + per-step XML files under
      references/steps/). Walks through discovery, type selection, and
      configuration with detailed guidance and examples for each skill type.
    </purpose>

    <output>
      A complete skill directory at .vera/skills/{skill_id}/ containing:
      - skill.yaml (vera-cli artifact descriptor)
      - head.md (the `--- name/description ---` frontmatter that surfaces in
        OpenCode's skill picker)
      - skill-overview.md (the workflow-engine-consumed body with overview,
        workflow steps, completion)
      - references/steps/step-NN-*.xml files (one per workflow step)
      - references/{additional}.md (skill-local references such as severity
        ladders, dispatch tables, format specs)
      - references/scripts/*.py (PEP 723 self-contained scripts when needed)
    </output>

    <key-responsibility>
      Two critical decisions shape every skill:

      1. SKILL TYPE — Determines structure and interaction:
         - workflow: Multi-step, checkpoint-driven, produces output
           incrementally. Has step files under references/steps/.
         - exec: Single-shot execution, returns result. No step files.
         - data: Reference material loaded on demand. No workflow,
           no scripts. Examples in dubstack: context-md-format,
           decision-record-format.

      2. SCRIPTS — Apply script-first mentality:
         If anything CAN be a script, it probably SHOULD be a script.
         Scripts are deterministic, token-efficient, and reliably
         repeatable. Dubstack scripts use PEP 723 inline metadata so they
         are self-contained — agents invoke them via `uv run`.

      Authoring discipline: references carry OPERATIONAL DATA only, not
      meta-commentary. No "this reference is consumed by skill X" intros.
      No "per Lock N" attributions on every sub-statement. No "What this
      table is NOT" meta-sections. Skill prompts carry intent; references
      carry data.
    </key-responsibility>
  </overview>

  <workflow>

    <step n="1" title="Discovery and Context">
      <action>Load and execute: references/steps/step-01-discovery.xml</action>
      <note>
        Gather requirements: what the skill does, which agent owns it, and
        whether there's a workflow spec (e.g., a ticketsmith / codesmith
        lock) the skill must conform to.
      </note>
    </step>

    <step n="2" title="Skill Type and Architecture" critical="true">
      <action>Load and execute: references/steps/step-02-type.xml</action>
      <note>
        THIS IS THE MOST CRITICAL STEP. Decisions made here:
        - Skill type (workflow / exec / data)
        - Script-first analysis (what SHOULD be scripts)
        - Script designs (name, purpose, inputs, outputs)
        - Reusable content plan (scripts, references, attachments)
      </note>
    </step>

    <step n="3" title="Scaffold Skill">
      <action>Load and execute: references/steps/step-03-scaffold.xml</action>
      <note>
        Create the skill directory and initial files following the dubstack
        layout. For workflow skills: skill.yaml + head.md + skill-overview.md
        + references/steps/. For exec: skill.yaml + head.md + skill-overview.md.
        For data: skill.yaml + SKILL.md (flat layout — see context-md-format).
        If shared/workflow-engine.md is missing in the project and the new
        skill is type=workflow, copy from bundled reference.
      </note>
    </step>

    <step n="4" title="Skill Identity">
      <action>Load and execute: references/steps/step-04-identity.xml</action>
      <note>
        Define name and description in head.md. The description is critical
        for discoverability — it helps the orchestrating agent know when to
        invoke this skill. Be specific about inputs, outputs, and the
        decision shape the skill resolves.
      </note>
    </step>

    <step n="5" title="Build Configuration">
      <action>Load and execute: references/steps/step-05-build-config.xml</action>
      <note>
        Configure skill.yaml: type/id/destination/file_name, includes
        (head.md + shared/workflow-engine.md + skill-overview.md for
        workflow skills; head.md + skill-overview.md for exec; SKILL.md
        for data), attachments (references/ for skill-local resources;
        shared/scripts/ if the skill invokes any shared script;
        shared/references/{namespace}/ for any cross-skill reference).
      </note>
    </step>

    <step n="6" title="Create Scripts" if="scripts_planned">
      <action>Load and execute: references/steps/step-06-create-scripts.xml</action>
      <note>
        Generate script files based on designs from Step 2. Each script
        gets PEP 723 header, docstring, and function stubs. Dubstack
        convention: scripts that are reusable across skills live in
        .vera/shared/scripts/; skill-local scripts live at
        references/scripts/. Both invoke `thoughts` CLI internally rather
        than asking the agent to pass thoughts metadata.
      </note>
    </step>

    <step n="7" title="Workflow Design" if="skill_type == 'workflow'">
      <action>Load and execute: references/steps/step-07-workflow-design.xml</action>
      <note>
        Design the workflow steps. Only for workflow-type skills. This is
        where we plan the user journey through the skill. Each step should
        have a clear purpose and produce a visible artifact or transition.
      </note>
    </step>

    <step n="8" title="Create Step Files" if="skill_type == 'workflow'">
      <action>Load and execute: references/steps/step-08-step-files.xml</action>
      <note>
        Generate the individual step files under references/steps/. Each
        step file uses the workflow-engine tag vocabulary (action, check,
        ask, invoke-skill, invoke-agent, template-output, goto). Follow the
        ticketsmith / codesmith step-file conventions for cross-skill
        consistency.
      </note>
    </step>

    <step n="9" title="Validate and Complete">
      <action>Load and execute: references/steps/step-09-validate.xml</action>
      <note>
        Run validation on the completed files. Verify skill.yaml includes
        resolve. Verify step files reference real action types. Update the
        relevant build group in .vera/vera.manifest.yaml.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      After all steps complete, present the user with:
      1. Location of the created skill files under .vera/skills/{skill_id}/
      2. Summary of the skill's type and structure
      3. Manifest update status
      4. Next steps: build, test, add to agent menu
    </action>

    <next-steps>
      <step>Build dubstack: `vera build`</step>
      <step>Add skill to the owning agent's frontmatter.md permission map and agent-body.md menu</step>
      <step>Test by invoking from the agent</step>
    </next-steps>
  </completion>

</skill>
