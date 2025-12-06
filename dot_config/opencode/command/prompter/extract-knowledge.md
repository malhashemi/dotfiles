---
description: Extracts valuable insights from the current conversation and integrates them into a specified agent's or skill's knowledge base
argument-hint: "[target-name-or-description]"
agent: prompter
---

## Variables

### Dynamic Variables
TARGET: $ARGUMENTS

## Instructions

ultrathink: Analyze the current conversation for patterns, lessons, and insights that would be valuable for the specified target, then systematically integrate them into that artifact's prompt or SKILL.md.

## Workflow

### Phase 1: Context Analysis

1. **Interpret Target Input**
   `{{TARGET}}` may be:
   - A file path: `.opencode/agent/architect.md`, `~/.config/opencode/skills/pr-review/SKILL.md`
   - A name: `architect`, `pr-review`
   - A description: "the skill we just worked on", "improve the pr-review skill"
   
   Resolve to actual file by checking:
   - `.opencode/agent/`, `~/.config/opencode/agent/` (agents)
   - `.opencode/command/`, `~/.config/opencode/command/` (commands)
   - `.opencode/skills/`, `~/.config/opencode/skills/` (skills → look for SKILL.md)
   
   If ambiguous or descriptive, infer from conversation context or ask user.

2. **Determine Artifact Type & Load Template**
   - Agent (has `mode:` in frontmatter) → Load `skills_prompter_agent_creator`
   - Command (in command/ directory, no mode) → Load `skills_prompter_command_creator`
   - Skill (has SKILL.md) → Load `skills_prompter_skill_creator`

3. **Read Target Artifact**
   - Read the resolved file
   - Understand its role, structure, and current knowledge
   - Identify what kinds of insights would be valuable

4. **Conversation Mining**
   Analyze the conversation for:
   - Patterns discovered through experience
   - Techniques that worked well
   - Mistakes that led to learning
   - Clarifications that improved understanding
   - Workflow optimizations discovered
   - Edge cases encountered
   Filter for relevance to the target artifact's domain

5. **Create Extraction Todos**
   Use **todowrite** to create systematic tracking:
   - Analyze conversation for target-relevant patterns
   - Identify high-value insights worth preserving
   - Present findings for user approval
   - Determine optimal placement in artifact's structure
   - Craft precise wording for additions
   - Implement approved changes
   
   Update todo status with **todowrite** as each phase completes.

### Phase 2: Knowledge Extraction

1. **Present Discovered Insights**
   ```markdown
   ## Knowledge Extraction for {{Artifact Name}}
   
   From this conversation, I've identified these valuable insights:
   
   ### 1. **{{Pattern/Lesson Title}}**
   {{Description of what was learned}}
   **Relevance**: {{Why this matters for this artifact}}
   **Example from conversation**: {{Brief example}}
   
   ### 2. **{{Next Pattern}}**
   [Continue for all significant findings]
   
   Which of these would you like to integrate into the target's knowledge base?
   ```

2. **⚠️ CHECKPOINT** - Await user selection of insights to keep

### Phase 3: Integration Planning

1. **Analyze Placement Options**
   For each approved insight, determine where it best fits:
   
   For agents:
   - Philosophy, Knowledge Base, Workflow, Learned Constraints
   
   For skills:
   - Overview, When to Use, Workflow Phases, Domain Patterns, references/ files
   
   For commands:
   - Instructions, Workflow phases, Notes

2. **Present Integration Plan**
   ```markdown
   ## Proposed Integration Plan
   
   **Insight 1**: {{title}}
   - Target Section: {{section}}
   - Rationale: {{why this section}}
   
   **Insight 2**: {{title}}
   - Target Section: {{section}}
   - Rationale: {{why this section}}
   
   Shall we proceed with these placements?
   ```

3. **⚠️ CHECKPOINT** - Await approval of placement strategy

### Phase 4: Wording Refinement

1. **Craft Precise Wording**
   For each insight, create the exact text to add using git-style diff format:
   ```markdown
   ## Proposed Additions
   
   ### For {{Section Name}}:
   ```diff
   @@ -{{line}},{{count}} +{{line}},{{new_count}} @@
   {{context}}
   +{{new_content}}
   {{context}}
   ```
   
   Do these wordings accurately capture the insights?
   ```

2. **⚠️ CHECKPOINT** - Await wording approval

### Phase 5: Implementation

1. **Execute Edits**
   - Add approved content to designated sections
   - Create new sections if needed (e.g., Learned Constraints)
   - Maintain template compliance throughout

2. **Verification**
   ```markdown
   ## ✅ Knowledge Integration Complete
   
   Added to {{Artifact Name}}:
   - {{Section}}: {{Brief description of addition}}
   - {{Section}}: {{Brief description of addition}}
   
   These insights from our conversation are now part of the target's operational knowledge.
   ```

## Selection Criteria

Only extract insights that are:
- **Reusable**: Will apply in future similar situations
- **Non-obvious**: Not already covered in agent's current knowledge
- **Validated**: Proven effective in this conversation
- **Relevant**: Within the agent's domain of responsibility
- **Significant**: Worth the complexity of adding to the prompt

## Note

This command focuses on experiential learning - patterns and techniques discovered through actual usage, not theoretical knowledge. The goal is continuous improvement of agents through captured experience.