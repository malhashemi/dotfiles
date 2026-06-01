<!-- ================================================================
     TEMPLATE: critical-rules
     PURPOSE:  Hard behavioral boundaries the subagent must never violate.
     REQUIRED: Subagents only. Primary agents use persona principles instead.
     NOTE:     These are NON-NEGOTIABLE rules. Unlike principles (which guide),
               critical rules CONSTRAIN. Violation = broken agent.
     ================================================================ -->

<critical-rules>
  <!-- FILL: critical rules
       Define the absolute behavioral boundaries for this subagent.
       Each rule is a hard constraint — not a suggestion.
       
       Format:
         <rule>CONSTRAINT in clear, unambiguous language</rule>
       
       Common categories:
       
       Autonomy rules (almost always needed for subagents):
         <rule>You are a SUB-AGENT — do NOT ask questions or interact with users</rule>
         <rule>Return findings in the exact output-contract format</rule>
       
       Quality rules (domain-specific):
         <rule>NEVER fabricate sources or citations — every URL must come from actual search results</rule>
         <rule>NEVER present training data as web-verified findings</rule>
         <rule>If searches return nothing useful, say so explicitly — do not fill gaps with assumptions</rule>
       
       Scope rules (prevent scope creep):
         <rule>Do NOT modify any files — read-only operations only</rule>
         <rule>Do NOT execute commands — use grep, glob, and list tools only</rule>
         <rule>Stay within the requested scan tasks — do not add unrequested analysis</rule>
       
       Output rules (ensure consistency):
         <rule>Include ALL sources used in the sources table</rule>
         <rule>Be thorough — 4-8 searches minimum per research area</rule>
         <rule>Report file paths relative to the project root</rule>
       
       Tips:
         - Write rules as if the agent WILL try to violate them
         - Be specific: "NEVER fabricate" not "try to be accurate"
         - Scope rules prevent the agent from doing too much (equally important as too little)
         - 4-8 rules is typical. Fewer = important ones stand out. More = noise.
  -->
</critical-rules>
