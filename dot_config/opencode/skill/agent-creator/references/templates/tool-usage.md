<!-- ================================================================
     TEMPLATE: tool-usage
     PURPOSE:  Provides specific guidance on how to use available tools.
     REQUIRED: Optional — only when the agent needs non-obvious tool
               usage patterns (e.g., MCP tool fallback chains, specific
               tool preferences, search strategies).
     NOTE:     Permissions are set in agent.yaml frontmatter. This section
               provides GUIDANCE on how to use the permitted tools, not
               which tools are available.
     ================================================================ -->

<tool-usage>
  <!-- FILL: tool usage guidance
       Describe specific tool usage patterns for this agent.
       Only include this when tool usage is non-obvious or strategic.
       
       Common patterns:
       
       Web search with fallback chain:
         <primary-search>
           Use brave_search for all initial searches. Execute multiple
           searches in parallel when targeting different sub-topics.
         </primary-search>
         <fallback-search>
           Switch to exa_web_search_exa when:
           - brave_search returns errors or rate limits
           - Results are insufficient or poor quality
           - Need more academic or technical sources
         </fallback-search>
         <content-extraction>
           Use exa_crawling_exa to fetch full page content from promising URLs.
           Prioritize: official documentation, industry reports, reputable analysis.
         </content-extraction>
       
       Read-only codebase exploration:
         <scanning>
           Use glob to discover file patterns. Use grep to search content.
           Use list to enumerate directories. Use read for file content.
           NEVER use bash — all exploration through dedicated tools.
         </scanning>
       
       Tips:
         - Only create this section when tool usage needs explanation
         - If tool usage is straightforward, skip this template
         - Focus on STRATEGY (when to use which tool, fallback chains)
         - Don't repeat permissions — those are in agent.yaml
  -->
</tool-usage>
