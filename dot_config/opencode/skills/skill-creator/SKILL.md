---
name: skill-creator
description: |
  Guide for creating effective skills with UV + justfile structure. This skill should be used 
  when users want to create a new skill (or update an existing skill) that extends the agent's 
  capabilities with specialized knowledge, workflows, or tool integrations. Skills include
  PEP 723 compliant Python scripts managed via justfile for consistent execution.
---

# Skill Creator

This skill provides guidance for creating effective skills using modern Python tooling.

## About Skills

Skills are modular, self-contained packages that extend the agent's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks—they transform a general-purpose agent into a specialized agent equipped with
procedural knowledge that no model can fully possess.

### What Skills Provide

1. **Specialized workflows** - Multi-step procedures for specific domains
2. **Tool integrations** - Instructions for working with specific file formats or APIs
3. **Domain expertise** - Company-specific knowledge, schemas, business logic
4. **Bundled resources** - Scripts, references, and assets for complex and repetitive tasks

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (name, description)
│   └── Markdown instructions
├── justfile (recommended)
│   └── Task recipes using `uv run` for script execution
└── Bundled Resources (optional)
    ├── scripts/      - PEP 723 Python scripts (uv run)
    ├── references/   - Documentation loaded into context as needed
    └── assets/       - Files used in output (templates, etc.)
```

#### SKILL.md (required)

**Metadata Quality:** The `name` and `description` in YAML frontmatter determine when the agent
will use the skill. Be specific about what the skill does and when to use it. Use the third-person
(e.g. "This skill should be used when..." instead of "Use this skill when...").

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Note**: Scripts may still need to be read by the agent for patching or environment-specific adjustments

##### References (`references/`)

Documentation and reference material intended to be loaded as needed into context to inform the agent's process and thinking.

- **When to include**: For documentation that the agent should reference while working
- **Examples**: `references/finance.md` for financial schemas, `references/mnda.md` for company NDA template, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps SKILL.md lean, loaded only when the agent determines it's needed
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window. Keep only essential procedural instructions and workflow guidance in SKILL.md; move detailed reference material, schemas, and examples to references files.

##### Assets (`assets/`)

Files not intended to be loaded into context, but rather used within the output the agent produces.

- **When to include**: When the skill needs files that will be used in the final output
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits**: Separates output resources from documentation, enables the agent to use files without loading them into context

### Script Standards

All scripts should follow PEP 723 inline metadata format:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
# ]
# ///
```

Execute scripts with `uv run {base_dir}/scripts/script.py [args]` - UV handles dependencies automatically.

**Important**: When a skill is loaded, the agent receives the base directory path. All script
references in SKILL.md should use `{base_dir}` placeholder to indicate the skill's root directory.

### Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed by the agent (unlimited)

## Scripts

The base directory for this skill is provided when loaded. Execute via justfile or directly with uv:

### Via Justfile (Recommended)

```bash
just -f {base_dir}/justfile <recipe> [args...]
```

| Recipe | Arguments | Description |
|--------|-----------|-------------|
| `init` | `skill_name path` | Initialize new skill at specified path |
| `init-global` | `skill_name` | Initialize in ~/.config/opencode/skills |
| `validate` | `skill_path` | Validate a skill's structure |
| `validate-all` | `skills_dir` | Validate all skills in a directory |

### Direct Execution

```bash
uv run {base_dir}/scripts/<script>.py [args...]
```

| Script | Arguments | Description |
|--------|-----------|-------------|
| `init_skill.py` | `skill_name --path path` | Initialize new skill at path |
| `quick_validate.py` | `skill_path` | Validate a skill's structure |

### Examples

```bash
# Via justfile (recommended)
just -f {base_dir}/justfile init-global my-new-skill
just -f {base_dir}/justfile validate ~/.config/opencode/skills/my-skill

# Direct execution
uv run {base_dir}/scripts/init_skill.py my-new-skill --path ~/.config/opencode/skills
uv run {base_dir}/scripts/quick_validate.py ~/.config/opencode/skills/my-skill
```

## Skill Creation Process

### Step 1: Understand the Skill

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

Before creating, gather concrete examples of how the skill will be used. Ask the user:

- "What functionality should this skill support?"
- "Can you give examples of how this skill would be used?"
- "What would a user say that should trigger this skill?"

For example, when building an image-editor skill:
- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"

Avoid overwhelming users with too many questions at once. Start with the most important and follow up as needed. Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Plan Reusable Contents

Analyze each example to identify what should be reusable:

| Resource Type | When to Include | Example |
|--------------|-----------------|---------|
| **scripts/** | Deterministic code rewritten repeatedly | `rotate_pdf.py` |
| **references/** | Documentation to load as needed | `schema.md` |
| **assets/** | Files used in output | `template.pptx` |

Example analyses:

- **pdf-editor skill** for "Help me rotate this PDF" → Rotating requires the same code each time → `scripts/rotate_pdf.py`
- **frontend-builder skill** for "Build me a todo app" → Same boilerplate each time → `assets/hello-world/` template
- **big-query skill** for "How many users logged in today?" → Re-discovering schemas each time → `references/schema.md`

### Step 3: Initialize the Skill

Skip this step only if the skill being developed already exists and iteration is needed. In this case, continue to the next step.

Ask the user where the skill should be created:

- **Global** (`~/.config/opencode/skills/`) - Available across all projects
- **Local** (project directory) - Specific to one project

```bash
# Global skill (available everywhere)
just -f {base_dir}/justfile init-global my-new-skill

# Local skill (project-specific)
just -f {base_dir}/justfile init my-new-skill ./skills
```

This creates:
- `SKILL.md` with template and TODOs
- `justfile` with example recipes
- `scripts/example.py` (PEP 723 template)
- `references/api_reference.md` (placeholder)
- `assets/example_asset.txt` (placeholder)

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of the agent to use. Focus on including information that would be beneficial and non-obvious to the agent. Consider what procedural knowledge, domain-specific details, or reusable assets would help another agent instance execute these tasks more effectively.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Also, delete any example files and directories not needed for the skill. The initialization script creates example files in `scripts/`, `references/`, and `assets/` to demonstrate structure, but most skills won't need all of them.

#### Update SKILL.md

**Writing Style:** Write the entire skill using **imperative/infinitive form** (verb-first instructions), not second person. Use objective, instructional language (e.g., "To accomplish X, do Y" rather than "You should do X" or "If you need to do X"). This maintains consistency and clarity for AI consumption.

To complete SKILL.md, answer the following questions:

1. What is the purpose of the skill, in a few sentences?
2. When should the skill be used?
3. In practice, how should the agent use the skill? All reusable skill contents developed above should be referenced so that the agent knows how to use them.

#### Create Scripts

For each script:
1. Add PEP 723 metadata block at top
2. Include docstring with usage and output description
3. Document in SKILL.md Scripts section with `{base_dir}` path references

Example script structure:
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Brief description.

Usage: uv run script.py <arg1> [arg2]
Output: Description of output
"""

import sys

def main():
    # Implementation
    pass

if __name__ == "__main__":
    main()
```

### Step 5: Validate

```bash
# Validate structure
just -f {base_dir}/justfile validate ~/.config/opencode/skills/my-skill

# Validate all skills in a directory
just -f {base_dir}/justfile validate-all ~/.config/opencode/skills
```

### Step 6: Iterate

After testing:
1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Update SKILL.md or scripts
4. Test again
