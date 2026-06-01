---
name: agent-creator
description: "Guides creation of dubstack agent source files (agent.yaml + frontmatter.md + agent-body.md) through discovery, template selection, and iterative filling. Produces complete vera-cli native agent directories ready for `vera build`. Self-documenting templates teach the fill conversation; the skill orchestrates the process while the templates own the content knowledge. Primary entry point for adding a new agent to dubstack."
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
<skill id="agent-creator" name="Agent Creator" version="2.0">

  <overview>
    <purpose>
      Guide creation of a new dubstack agent through discovery, template
      selection, and iterative filling. Produces the complete source files:
      agent.yaml (vera-cli native build descriptor) + frontmatter.md (YAML
      frontmatter as raw content) + agent-body.md (activation block, persona,
      menu).
    </purpose>

    <output>
      A complete agent source directory under .vera/agents/{agent_id}/
      containing agent.yaml, frontmatter.md, and agent-body.md, plus any
      additional include files the agent needs. The manifest gets updated
      with the new agent's artifact entry.
    </output>

    <key-principles>
      <principle>
        Templates are self-documenting — each content template under
        references/templates/ contains embedded FILL instructions that teach
        how to fill every section. The skill orchestrates the process; the
        templates own the content knowledge.
      </principle>
      <principle>
        Shared structural blocks live in dubstack's .vera/shared/ —
        activation.md, workflow-engine.md, baseline/context-md-awareness.md,
        baseline/thoughts-cli-awareness.md. New agents reference these via
        the agent.yaml `includes:` list rather than duplicating content.
      </principle>
      <principle>
        Persona principles are MENTAL POSTURE, not rule lists. The persona
        template's FILL instructions warn explicitly against rule-list drift
        (workflow constraints disguised as principles). Push back during the
        fill conversation when the user proposes bolded-name commandments —
        those belong in skill prompts or activation rules, not in the
        persona block.
      </principle>
      <principle>
        Cross-template consistency is enforced before completion: skills
        named in agent.yaml permissions must appear in the menu; menu skill
        names must match real skill IDs under .vera/skills/; subagent input
        contracts must be parseable by the orchestrator that will dispatch
        them.
      </principle>
    </key-principles>
  </overview>

  <workflow>

    <step n="1" title="Discovery & Context">
      <action>Load and execute: references/steps/step-01-discovery.xml</action>
      <note>
        Gather requirements, determine mode (primary/subagent), identify
        skills. Check for architecture documents (workflow specs,
        implementation specs) the agent must conform to.
      </note>
    </step>

    <step n="2" title="Template Selection">
      <action>Load and execute: references/steps/step-02-template-selection.xml</action>
      <note>
        Auto-select structural templates by mode. Auto-select required
        content templates (persona + menu for primary; persona +
        subagent-instructions for subagent). Detect missing project
        infrastructure (shared/activation.md, shared/agent-activation.md,
        shared/agent-close.md, shared/baseline/*) and copy from bundled
        references when absent. Confirm the composition order in
        agent.yaml includes.
      </note>
    </step>

    <step n="3" title="Scaffold & Configure">
      <action>Load and execute: references/steps/step-03-scaffold.xml</action>
      <note>
        Gather identity (agent_id, name, title, emoji). Configure
        frontmatter (mode, color, permission map). Write agent.yaml with
        includes. For primary agents, includes typically begin with
        frontmatter.md, then shared/activation.md, then any
        shared/baseline/* fragments the agent needs, then agent-body.md.
      </note>
    </step>

    <step n="4" title="Fill Content Templates" critical="true">
      <action>Load and execute: references/steps/step-04-fill-process.xml</action>
      <note>
        THIS IS THE CRAFT STEP. Work through each selected content template,
        reading its embedded FILL instructions, discussing each section with
        the user, and writing quality content. The persona template's
        instructions are particularly important — they encode the BMAD
        mental-posture convention for principles.
      </note>
    </step>

    <step n="5" title="Validate & Complete">
      <action>Load and execute: references/steps/step-05-validate.xml</action>
      <note>
        Verify files exist with expected structure. Cross-reference
        consistency between agent.yaml permissions, menu items, and skills.
        Run `vera build` in a dry-run mode if available to surface
        compile-time issues before declaring the agent complete. Update the
        relevant build group in .vera/vera.manifest.yaml.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      After all steps complete, present the user with:
      1. Location of the created agent source files under .vera/agents/{agent_id}/
      2. Summary of identity, skills, and template composition
      3. Whether the manifest was updated and which build group received the entry
      4. Next steps: create skills via [CS], build dubstack, test in OpenCode
    </action>

    <next-steps>
      <step>Create each new skill the agent depends on via [CS] Create Skill</step>
      <step>Build dubstack: `vera build`</step>
      <step>Verify the compiled artifact at the configured output path</step>
      <step>Test in OpenCode by switching to the new agent</step>
    </next-steps>
  </completion>

</skill>
