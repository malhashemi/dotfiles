<!-- ================================================================
     TEMPLATE: input-output-contracts
     PURPOSE:  Defines what the subagent receives and what it returns.
     REQUIRED: Subagents only. Primary agents do NOT use contracts.
     NOTE:     These contracts are the API between orchestrator and
               subagent. Be precise — the orchestrator parses the output.
     ================================================================ -->

<input-contract>
  <!-- FILL: input-contract description
       Describe what the orchestrating agent passes to this subagent.
       "The orchestrating agent provides a structured request.
        Parse the prompt for these fields:"
  -->
  <description>
  </description>

  <fields>
    <!-- FILL: input fields
         Define each field the orchestrator provides.
         Mark required vs optional. Describe format and valid values.
         
         Format:
           <field name="field_name" required="true|false">Description of field</field>
         
         Examples:
           <field name="research_type" required="true">One of: market, domain, technical</field>
           <field name="topic" required="true">The overall research topic</field>
           <field name="scope_context" required="false">Additional context about scope or priorities</field>
           <field name="scan_tasks" required="true">Comma-separated list of scan tasks to execute</field>
         
         Tips:
           - Required fields should be the minimum needed to execute
           - Optional fields provide additional context or customization
           - Use clear value constraints: "One of: x, y, z" or "Comma-separated list"
    -->
  </fields>
</input-contract>

<output-contract>
  <!-- FILL: output-contract description
       Describe what this subagent returns to the orchestrator.
       "Return a structured report for the requested task.
        The orchestrating agent will integrate this into the final document."
  -->
  <description>
  </description>

  <format>
    <!-- FILL: output format
         Define the EXACT format the subagent returns. Be very specific —
         the orchestrator needs to parse or integrate this output.
         
         Use markdown structure with clear section headers.
         Include placeholder descriptions for dynamic content.
         
         Example (research subagent):
           ## Research Findings: {area}
           ### Summary
           {2-3 sentence overview}
           ### Detailed Findings
           #### {Sub-topic 1}
           {Analysis with inline citations}
           ### Sources Used
           | # | Source | URL | Type | Reliability |
           ### Confidence Assessment
           - High Confidence Claims: {count}
         
         Example (scanner subagent):
           ## Scan Report: {task_name}
           ### Findings
           {Structured results per scan task}
           ### File Inventory
           | Path | Type | Size | Description |
         
         Tips:
           - Use tables for structured data the orchestrator will reference
           - Use headers the orchestrator can find with string matching
           - Include metadata sections (confidence, gaps, limitations)
    -->
  </format>
</output-contract>
