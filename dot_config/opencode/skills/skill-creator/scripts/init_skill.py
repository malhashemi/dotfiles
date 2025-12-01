# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Skill Initializer - Creates a new skill from template with PEP 723 Python scripts and justfile.

Usage:
    uv run init_skill.py <skill-name> --path <path>

Examples:
    uv run init_skill.py my-new-skill --path ~/.config/opencode/skills
    uv run init_skill.py my-api-helper --path ./skills
"""

import sys
from pathlib import Path


JUSTFILE_TEMPLATE = """# {skill_title} - Task Runner
# Run tasks with: just -f {{base_dir}}/justfile <recipe> [args...]

# Default recipe - show help
default:
    @just --list

# Directory containing scripts
scripts_dir := justfile_directory() / "scripts"

# Example recipe - replace with actual recipes
example name="world":
    uv run {{{{scripts_dir}}}}/example.py {{{{name}}}}

# [TODO: Add more recipes as needed]
# recipe-name arg1 arg2="default":
#     uv run {{{{scripts_dir}}}}/script_name.py {{{{arg1}}}} {{{{arg2}}}}
"""

SKILL_TEMPLATE = """---
name: {skill_name}
description: |
  [TODO: Complete and informative explanation of what the skill does and when to use it.
  This skill should be used when... Include specific scenarios, file types, or tasks that trigger it.]
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## When to Use

- [TODO: Specific trigger scenario 1]
- [TODO: Specific trigger scenario 2]
- [TODO: Specific trigger scenario 3]

## Scripts

All scripts are PEP 723 compliant Python files. The base directory for this skill is provided
when loaded. Execute via justfile or directly with uv:

### Via Justfile (Recommended)

```bash
just -f {{base_dir}}/justfile <recipe> [args...]
```

| Recipe | Arguments | Description |
|--------|-----------|-------------|
| `example` | `[name]` | Example recipe - replace with actual recipes |

### Direct Execution

```bash
uv run {{base_dir}}/scripts/<script>.py [args...]
```

| Script | Arguments | Description |
|--------|-----------|-------------|
| `example.py` | `[name]` | Example script - replace with actual scripts |

### Example

```bash
# Via justfile
just -f {{base_dir}}/justfile example world

# Direct execution
uv run {{base_dir}}/scripts/example.py world
```

## [TODO: Main Section]

[TODO: Add workflow, tasks, or capabilities based on skill structure pattern:

**Workflow-Based** (sequential processes):
- Step 1 → Step 2 → Step 3

**Task-Based** (tool collections):
- Task Category 1
- Task Category 2

**Capabilities-Based** (integrated features):
- ### 1. Feature One
- ### 2. Feature Two
]

## Error Handling

- [TODO: Common error 1] → [Solution]
- [TODO: Common error 2] → [Solution]
"""

EXAMPLE_SCRIPT = '''# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Example script for {skill_name}.

Usage: uv run example.py [name]
Output: Greeting message

Replace this with actual implementation or delete if not needed.
"""

import sys


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "world"
    print(f"Hello, {{name}}! This is an example script for {skill_name}.")
    # TODO: Add actual script logic here


if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases

## Structure Suggestions

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Troubleshooting
- Best practices
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output Claude produces.

## Common Asset Types

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Data files: .csv, .json, .xml, .yaml

Note: This is a text placeholder. Actual assets can be any file type.
"""


def title_case_skill_name(skill_name: str) -> str:
    """Convert hyphenated skill name to Title Case for display."""
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def init_skill(skill_name: str, path: str) -> Path | None:
    """
    Initialize a new skill directory with PEP 723 Python scripts and justfile.

    Args:
        skill_name: Name of the skill (hyphen-case)
        path: Path where the skill directory should be created

    Returns:
        Path to created skill directory, or None if error
    """
    skill_dir = Path(path).resolve() / skill_name

    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return None

    skill_title = title_case_skill_name(skill_name)

    # Create SKILL.md
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name, skill_title=skill_title
    )
    try:
        (skill_dir / "SKILL.md").write_text(skill_content)
        print("✅ Created SKILL.md")
    except Exception as e:
        print(f"❌ Error creating SKILL.md: {e}")
        return None

    # Create justfile
    justfile_content = JUSTFILE_TEMPLATE.format(skill_title=skill_title)
    try:
        (skill_dir / "justfile").write_text(justfile_content)
        print("✅ Created justfile")
    except Exception as e:
        print(f"❌ Error creating justfile: {e}")
        return None

    # Create scripts/ with example PEP 723 script
    try:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / "example.py"
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
        print("✅ Created scripts/example.py (PEP 723)")
    except Exception as e:
        print(f"❌ Error creating scripts/: {e}")
        return None

    # Create references/ with example doc
    try:
        references_dir = skill_dir / "references"
        references_dir.mkdir(exist_ok=True)
        (references_dir / "api_reference.md").write_text(
            EXAMPLE_REFERENCE.format(skill_title=skill_title)
        )
        print("✅ Created references/api_reference.md")
    except Exception as e:
        print(f"❌ Error creating references/: {e}")
        return None

    # Create assets/ with example placeholder
    try:
        assets_dir = skill_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        (assets_dir / "example_asset.txt").write_text(EXAMPLE_ASSET)
        print("✅ Created assets/example_asset.txt")
    except Exception as e:
        print(f"❌ Error creating assets/: {e}")
        return None

    print(f"\n✅ Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    print("2. Add PEP 723 scripts to scripts/ and add recipes to justfile")
    print("3. Customize or delete example files in scripts/, references/, and assets/")
    print(
        f"4. Validate: uv run ~/.config/opencode/skills/skill-creator/scripts/quick_validate.py {skill_dir}"
    )

    return skill_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != "--path":
        print("Usage: uv run init_skill.py <skill-name> --path <path>")
        print("\nSkill name requirements:")
        print("  - Hyphen-case identifier (e.g., 'data-analyzer')")
        print("  - Lowercase letters, digits, and hyphens only")
        print("  - Max 40 characters")
        print("\nExamples:")
        print("  uv run init_skill.py my-new-skill --path ~/.config/opencode/skills")
        print("  uv run init_skill.py my-api-helper --path ./skills")
        sys.exit(1)

    skill_name = sys.argv[1]
    path = sys.argv[3]

    print(f"🚀 Initializing skill: {skill_name}")
    print(f"   Location: {path}")
    print()

    result = init_skill(skill_name, path)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
