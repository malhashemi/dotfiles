<!-- ================================================================
     TEMPLATE: thoughts-context
     PURPOSE:  Integrates the agent with the thoughts system for
               artifact output and workflow tracking.
     REQUIRED: Optional — only for agents that output to thoughts.
     NOTE:     Uses {{team_name}} variable which must be defined
               in vera.config.yaml at the project level.
     ================================================================ -->

<context id="thoughts-system">
  <!-- FILL: thoughts-system context
       Describe how this agent uses the thoughts system.
       Include:
       - Which skills output artifacts and to which subdirectories
       - How to get metadata (always via thoughts metadata command)
       - How to validate and track
       
       Example (analyst agent):
         All workflow artifacts are output to the team's shared directory.
         Each skill specifies its output subdirectory name:
         - Brainstorming sessions → brainstorm/
         - Research reports → research/
         - Product briefs → briefs/
         - Project documentation → documentation/
         
         Run `thoughts metadata --team {{team_name}}` to get:
         - shared_folder path (base directory for all output)
         - Valid frontmatter field values and schema
         - Pre-filled values (date, owner)
         
         The full output path = shared_folder + skill's output subdirectory.
         
         Use `thoughts validate` to verify frontmatter correctness.
         Use `thoughts backlog` commands for workflow state tracking.
       
       Tips:
         - NEVER hardcode the shared_folder path — always get it from metadata
         - NEVER hardcode frontmatter schema — always get it from metadata
         - List all output subdirectories so the agent knows where each goes
         - Include the validate and backlog commands for completeness
  -->
</context>
