---
description: Verifies template compliance of an agent/command/skill that has been worked on in the current conversation
argument-hint: "[optional-path-or-name]"
agent: prompter
---

## Variables

### Dynamic Variables
TARGET: $ARGUMENTS

## Instructions

Perform a comprehensive template compliance verification of the artifact that has been modified in this conversation. Build a dynamic checklist based on the actual template requirements.

**If {{TARGET}} provided**: Use as target path/name hint
**If no arguments**: Infer target from recent conversation context

## Workflow

1. **Identify Target Artifact**
   - Look through recent conversation to identify which prompt file was being worked on
   - If {{TARGET}} provided, use as hint for location
   - Read the current state of that file
   - Determine artifact type:
     - Skill: File is SKILL.md or in skills/ directory
     - Agent: Has mode: field in frontmatter
     - Command: In command/ directory, no mode field

2. **Create Base Compliance Checklist**
   Start with universal checks and add them to your todo list using todowrite:
   ```
   ## Universal Compliance Checks
   - [ ] Frontmatter exists and is properly formatted
   - [ ] Mode field matches file location (agents only)
   - [ ] Description field is comprehensive and searchable
   - [ ] Tools section lists appropriate permissions (agents only)
   - [ ] Variables defined are actually utilized in the prompt
   - [ ] No residual content from old versions
   - [ ] Emphasis keywords (CRITICAL, IMPORTANT, ALWAYS, NEVER) used strategically
   - [ ] Section sequence matches the template exactly
   - [ ] Section names match template formatting
   
   ## Skill-Specific Checks (if applicable)
   - [ ] SKILL.md follows skill template structure
   - [ ] references/ files are appropriately sized and organized
   - [ ] scripts/ follow PEP 723 format with proper metadata
   - [ ] Progressive disclosure: lean SKILL.md, detailed references/
   ```

3. **Add Template-Specific Checks**
   Load the appropriate template skill to get exact structure:
   - For agents: `skills_prompter_agent_creator`
   - For commands: `skills_prompter_command_creator`
   - For skills: `skills_prompter_skill_creator`
   
   Then analyze deeply:
   - What structural patterns are mandatory?
   - What formatting rules apply?
   - Instructions followed in each section?

   Then dynamically add todos for each template-specific requirement discovered through analysis. Let the actual template guide what needs to be verified rather than following predetermined checks.

4. **Execute Verification**
   Work through each todo item systematically using todoread/todowrite:
   - Mark as in_progress
   - Perform the specific check against the template
   - Document any deviations found
   - Mark as complete
   - Update todo list as you progress

5. **Generate Compliance Report**
   ```markdown
   ## Template Compliance Report: [Artifact Name]

   **Template Type**: [primary-agent | subagent | command]
   **File Path**: [location]

   ### ✅ Compliant Areas:
   - [List what matches template requirements]

   ### ❌ Issues Found:
   - **[Issue Category]**: [Specific problem]
     - Location: Line [X]
     - Expected: [What template requires]
     - Found: [What's actually there]

   ### 🔧 Recommended Fixes:
   1. [Specific actionable fix]
   2. [Next fix with clear instructions]

   ### Verification Checklist Status:
   - Completed: [X/Y] checks
   - Issues found: [N]

   ### Overall Status: [✅ COMPLIANT | ⚠️ MINOR ISSUES | ❌ NEEDS FIXES]
   ```

   ⚠️ **CHECKPOINT** - Present compliance report and wait for user review before offering remediation

6. **Offer Remediation**
   If issues found: "Would you like me to fix these compliance issues now? I can address them in priority order using git-style diff format."

## Note

This command adapts to any template type by dynamically building its checklist. The base checks ensure fundamental compliance, while template-specific checks are discovered through deep analysis of the actual template loaded via skills, not predetermined rules.
