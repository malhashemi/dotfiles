---
name: extract-knowledge
description: "Extracts reusable patterns, conventions, and knowledge from existing artifacts (code, docs, prompts, conversations) into structured reference materials. The critical skill is PATTERN RECOGNITION — identifying what's reusable beyond the source material, actionable enough to guide future work, and structured for easy retrieval. Used when learning from examples to create templates, guidelines, or patterns; or when distilling a conversation into a teachable refinement."
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
<skill id="extract-knowledge" name="Extract Knowledge" version="1.0">

  <overview>
    <purpose>
      Extract reusable patterns, conventions, and knowledge from existing
      artifacts. Transform implicit knowledge into explicit, structured
      reference materials that can be used by agents, skills, and future
      prompt engineering.

      Second mode — diagnose a design flaw in an existing agent or skill:
      not only spot the issue but localize WHERE in the source it lives and
      prescribe WHAT to change. Output is an actionable remediation (exact
      source files + changes); the researcher is dispatched to map the source
      precisely (step 2).
    </purpose>

    <output>
      A knowledge document under .vera/shared/references/{namespace}/ or
      under a specific skill's references/ directory (depending on scope —
      cross-skill references go to shared; skill-local references stay in
      the skill). The document captures extracted patterns, examples, and
      guidelines with rationale.
    </output>

    <key-responsibility>
      The critical skill is PATTERN RECOGNITION — identifying what's:

      1. REUSABLE — Patterns that apply beyond the source material
      2. ACTIONABLE — Concrete enough to guide future work
      3. STRUCTURED — Organized for easy reference and retrieval

      Good extracted knowledge captures the "why" behind patterns, not just
      the "what" — enabling adaptation, not just copying. Distinguish from
      a transcript dump: extraction is synthesis, not pasting.

      When fixing an existing agent/skill, two disciplines apply: (1) VERIFY a
      dispatched researcher's load-bearing claims with a cheap deterministic
      probe before acting — a finding is a hypothesis until confirmed, and
      attribution is often subtly wrong; (2) prefer PREVENTION over validation
      — eliminate the error class at its source (a script, a structural
      guarantee) rather than adding a downstream check.
    </key-responsibility>
  </overview>

  <knowledge-types>

    <type name="patterns">
      <description>Recurring solutions to common problems</description>
      <sources>Code, architecture docs, successful implementations</sources>
      <output>Pattern catalog with context, structure, examples</output>
      <example>Error handling patterns, API design patterns</example>
    </type>

    <type name="conventions">
      <description>Agreed standards and naming/formatting rules</description>
      <sources>Style guides, existing codebases, team practices</sources>
      <output>Convention reference with rules and examples</output>
      <example>Naming conventions, file organization, commit formats</example>
    </type>

    <type name="templates">
      <description>Reusable structures with fill-in-the-blank sections</description>
      <sources>Successful documents, repeated file structures</sources>
      <output>Template with placeholders and usage instructions</output>
      <example>PR template, agent config template, skill template</example>
    </type>

    <type name="guidelines">
      <description>Decision-making frameworks and best practices</description>
      <sources>Post-mortems, lessons learned, expert knowledge</sources>
      <output>Guideline document with rationale and examples</output>
      <example>When to use X vs Y, security guidelines</example>
    </type>

    <type name="vocabulary">
      <description>Domain terms, definitions, and relationships</description>
      <sources>Documentation, conversations, domain experts</sources>
      <output>Glossary or ontology with definitions</output>
      <example>Project-specific terms, API concepts</example>
    </type>

    <type name="remediation">
      <description>A precise fix for a design flaw in an existing agent/skill</description>
      <sources>A surfaced defect + the agent/skill's true source under .vera/</sources>
      <output>A remediation set: exact source files and the change to each</output>
      <example>A workflow that ships process notes inside its deliverable</example>
    </type>

  </knowledge-types>

  <workflow>

    <step n="1" title="Discovery and Scoping">
      <action>Load and execute: references/steps/step-01-discovery.xml</action>
      <note>
        Identify what to extract from and what kind of knowledge we're
        after. Scope appropriately — too broad yields shallow results.
      </note>
    </step>

    <step n="2" title="Analysis and Pattern Recognition">
      <action>Load and execute: references/steps/step-02-analysis.xml</action>
      <note>
        THIS IS THE CORE STEP. Analyze source material for:
        - Recurring patterns
        - Implicit conventions
        - Decision rationales
        - Reusable structures
      </note>
    </step>

    <step n="3" title="Extraction and Structuring">
      <action>Load and execute: references/steps/step-03-extraction.xml</action>
      <note>
        Transform analysis into structured knowledge document. Include
        context, examples, and rationale — not just rules. Place output
        per dubstack convention: cross-skill knowledge under
        .vera/shared/references/{namespace}/; skill-local knowledge inside
        the owning skill's references/.
      </note>
    </step>

    <step n="4" title="Validate and Complete">
      <action>Load and execute: references/steps/step-04-validate.xml</action>
      <note>
        Verify extracted knowledge is accurate, actionable, and useful.
        Consider how it will be consumed by agents/skills.
      </note>
    </step>

  </workflow>

  <completion>
    <action>
      After all steps complete, present the user with:
      1. Location of the created knowledge document
      2. Summary of what was extracted
      3. Suggestions for which existing skills/agents should attach this reference
    </action>

    <next-steps>
      <step>Review and refine the extracted knowledge</step>
      <step>Add to skill references/ if skill-specific</step>
      <step>Add to .vera/shared/references/ if broadly applicable</step>
      <step>Update relevant skill.yaml attachments lists to consume the new reference</step>
    </next-steps>
  </completion>

</skill>
