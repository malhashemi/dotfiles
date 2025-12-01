---
name: skill-creator
description: |
  Guide for creating effective skills with UV + justfile structure. This skill should be used 
  when users want to create a new skill (or update an existing skill) that extends Claude's 
  capabilities with specialized knowledge, workflows, or tool integrations. Skills include
  PEP 723 compliant Python scripts managed via justfile for consistent execution.
---

# Skill Creator

This skill provides guidance for creating effective skills using modern Python tooling.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing
specialized knowledge, workflows, and tools. They transform Claude from a general-purpose 
agent into a specialized agent equipped with procedural knowledge.

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
3. **Bundled resources** - As needed by Claude (unlimited)

## Scripts

The base directory for this skill is provided when loaded. Execute scripts using `uv run`:

```bash
uv run {base_dir}/scripts/<script>.py [args...]
```

### Available Scripts

| Script | Arguments | Description |
|--------|-----------|-------------|
| `init_skill.py` | `skill_name --path path` | Initialize new skill at path |
| `quick_validate.py` | `skill_path` | Validate a skill's structure |
| `package_skill.py` | `skill_path [output_dir]` | Create distributable zip |

### Example Execution

```bash
# Initialize a new skill
uv run {base_dir}/scripts/init_skill.py my-new-skill --path ~/.config/opencode/skills

# Validate a skill
uv run {base_dir}/scripts/quick_validate.py ~/.config/opencode/skills/my-skill

# Package a skill for distribution
uv run {base_dir}/scripts/package_skill.py ~/.config/opencode/skills/my-skill ./dist
```

## Skill Creation Process

### Step 1: Understand the Skill

Before creating, understand concrete examples of how the skill will be used:

- What functionality should the skill support?
- What would a user say that should trigger this skill?
- What specific scenarios, file types, or tasks are involved?

### Step 2: Plan Reusable Contents

Analyze each example to identify what should be reusable:

| Resource Type | When to Include | Example |
|--------------|-----------------|---------|
| **scripts/** | Deterministic code rewritten repeatedly | `rotate_pdf.py` |
| **references/** | Documentation to load as needed | `schema.md` |
| **assets/** | Files used in output | `template.pptx` |

### Step 3: Initialize the Skill

```bash
# Initialize in global opencode directory
uv run {base_dir}/scripts/init_skill.py my-new-skill --path ~/.config/opencode/skills

# Or specify custom path
uv run {base_dir}/scripts/init_skill.py my-new-skill --path ./skills
```

This creates:
- `SKILL.md` with template and TODOs
- `scripts/example.py` (PEP 723 template)
- `references/api_reference.md` (placeholder)
- `assets/example_asset.txt` (placeholder)

### Step 4: Edit the Skill

#### Writing Style

Write using **imperative/infinitive form** (verb-first instructions):
- ✅ "To accomplish X, do Y"
- ❌ "You should do X" or "If you need to do X"

#### Update SKILL.md

Answer these questions:
1. What is the purpose of the skill? (2-3 sentences)
2. When should the skill be used? (trigger scenarios)
3. How should Claude use the skill? (reference all scripts)

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

### Step 5: Validate and Package

```bash
# Validate structure
uv run {base_dir}/scripts/quick_validate.py ~/.config/opencode/skills/my-skill

# Package for distribution
uv run {base_dir}/scripts/package_skill.py ~/.config/opencode/skills/my-skill ./dist
```

### Step 6: Iterate

After testing:
1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Update SKILL.md or scripts
4. Test again

## Bundled Resources

### scripts/

PEP 723 Python scripts executed via `uv run`.

- **When to include**: Deterministic code being rewritten repeatedly
- **Benefits**: Token efficient, no context loading needed
- **Format**: PEP 723 inline metadata for dependencies

### references/

Documentation loaded into context as needed.

- **When to include**: Detailed docs Claude should reference
- **Examples**: API docs, schemas, workflow guides
- **Best practice**: Keep SKILL.md lean, move details here

### assets/

Files used in output, not loaded into context.

- **When to include**: Templates, images, boilerplate
- **Examples**: `.pptx` templates, logo files, starter code
