---
description: Research an external repository to learn patterns and implementations
argument-hint: "[repo-url-or-name] [research-question]"
agent: researcher
---

## Variables

### Static Variables

CATALOG_PATH: "thoughts/global/extern/catalog.md"
RESEARCH_OUTPUT: "thoughts/global/extern/repos/"
WORKSPACE: ".extern/"
SKILL_DIR: "~/.config/opencode/skills/extern-researcher"

### Dynamic Variables

- ARGUMENTS = $ARGUMENTS
  argument-hint: "[repo-url-or-name] [research-question]"

REPO_INPUT: [first argument - URL, org/repo, or name of already-cloned repo]
RESEARCH_QUESTION: [remaining arguments - what to research about this repo]

## Instructions

Research an external repository following the extern-researcher skill workflow.

### Phase 1: Load Skill & Check Catalog

1. **Invoke the extern-researcher skill** to get full workflow guidance
2. **Read the global catalog** at `{{CATALOG_PATH}}`
3. **Search for existing research** on this repo:
   - Match by URL, repo name, or topic related to {{RESEARCH_QUESTION}}
   - If found: Read existing research documents
   - Evaluate: Is existing research sufficient for {{RESEARCH_QUESTION}}?

**If existing research is sufficient**:
- Summarize relevant findings for the user
- Ask if they want additional research or if this answers their question
- Skip to reporting if satisfied

**If existing research is insufficient or not found**:
- Proceed to Phase 2

### Phase 2: Initialize Workspace

1. **Check if `{{WORKSPACE}}` exists** in current project
2. **If not, create it**:
   ```bash
   mkdir -p {{WORKSPACE}}
   ```
3. **MUST copy AGENTS.md template** to workspace:
   ```bash
   cp {{SKILL_DIR}}/assets/workspace-agents.md {{WORKSPACE}}AGENTS.md
   ```
4. **Ensure .gitignore** includes `{{WORKSPACE}}`

### Phase 3: Clone Repository

1. **Parse {{REPO_INPUT}}** to extract:
   - Repository URL (if provided as URL)
   - Organization and repo name
   - Any branch/tag specifiers

2. **Derive directory name**: `{org}-{repo}` format
   - `https://github.com/facebook/react` → `facebook-react`
   - `vercel/next.js` → `vercel-next-js`

3. **Check if already cloned** in `{{WORKSPACE}}`

4. **Clone if needed** (shallow for efficiency):
   ```bash
   git clone --single-branch --depth 1 {url} {{WORKSPACE}}{org-repo}/
   ```

### Phase 4: Research

1. **Focus investigation** on: {{RESEARCH_QUESTION}}

2. **Use appropriate subagents**:
   - `codebase-pattern-finder` - Find implementations and usage examples
   - `codebase-analyzer` - Deep dive on specific components
   - `codebase-locator` - Navigate to relevant files

3. **Document findings** with specific file:line references

4. **Connect to context** - How do findings apply to current project needs?

### Phase 5: Persist Research

1. **Create research document**:
   - Directory: `{{RESEARCH_OUTPUT}}{org-repo}/`
   - Filename: `{YYYY-MM-DD}_{topic-slug}.md`
   - Use research document template from skill

2. **Update global catalog** using skill script:
   ```bash
   just -f {{SKILL_DIR}}/justfile add-study \
     "{org/repo}" \
     "{url}" \
     "{topic}" \
     "repos/{org-repo}/{filename}" \
     "{context}"
   ```

3. **Sync thoughts**:
   ```bash
   thoughts sync
   ```

### Phase 6: Report

Present findings to user:
- Summary of key discoveries
- Links to research document
- Suggestions for applying patterns to current project

## Important Notes

- **ALWAYS check catalog first** - Avoid duplicate research
- **Research persists, clones don't** - The `.extern/` workspace is temporary
- **Update catalog** - Every study must be recorded for future discovery
- **Use shallow clones** - Unless full git history is needed
