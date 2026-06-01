<!-- ================================================================
     TEMPLATE: execution
     PURPOSE:  Defines how the subagent processes its input.
     REQUIRED: Subagents only. Primary agents do NOT use this.
     NOTE:     These are the operational steps the subagent follows
               after receiving input. Keep it concise and sequential.
     ================================================================ -->

<execution>
  <!-- FILL: execution actions
       Define the sequential steps the subagent takes to process input.
       Each action is one clear operational step.
       
       Format:
         <action>Step description</action>
       
       Common patterns:
         1. Parse input → identify fields from input-contract
         2. Load skill → reference the skill for methodology
         3. Route → determine which methodology/track to follow
         4. Execute → perform the actual work
         5. Return → format and return results per output-contract
       
       Examples (web researcher):
         <action>Parse the input to identify research_type, topic, area, scope_context</action>
         <action>Load skill: web-research</action>
         <action>Follow the skill's type-routing to find the matching step file</action>
         <action>Execute the research methodology and return structured findings</action>
       
       Examples (codebase scanner):
         <action>Parse the input to identify project_root and scan_tasks</action>
         <action>Load skill: codebase-scan</action>
         <action>Execute each requested scan task using the skill's methodology</action>
         <action>Return combined scan results per output-contract format</action>
       
       Tips:
         - Keep actions high-level — the skill has the detailed methodology
         - The execution section is a routing/dispatch layer, not the full process
         - Always reference loading the skill — that's where the real work is defined
  -->
</execution>
