# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Scaffold a new command file by reading the YAML template.

Usage: uv run scaffold_command.py <name> --path <path> --agent <agent>

Arguments:
    name    Command name in kebab-case (e.g., 'run-tests')
    --path  Directory to create the command file
    --agent Agent that executes this command (e.g., 'build', 'prompter')

Output: Creates a markdown file with the command skeleton structure derived from the YAML template.

Examples:
    uv run scaffold_command.py run-tests --path .opencode/command --agent build
    uv run scaffold_command.py review-prompt --path .opencode/command/prompter --agent prompter
"""

import argparse
import sys
from pathlib import Path
import yaml


def load_template() -> dict:
    """Load the command YAML template."""
    script_dir = Path(__file__).parent
    references_dir = script_dir.parent / "references"

    template_file = references_dir / "command.yaml"

    if not template_file.exists():
        print(f"Error: Template file not found: {template_file}", file=sys.stderr)
        sys.exit(1)

    with open(template_file) as f:
        return yaml.safe_load(f)


def generate_frontmatter(
    template: dict, name: str, agent: str, include_args: bool = False
) -> str:
    """Generate frontmatter from template."""
    lines = ["---"]
    lines.append(f'description: "TODO: Add description for {name}"')

    if include_args:
        lines.append('argument-hint: "[argument-description]"')

    lines.append(f"agent: {agent}")
    lines.append("---")

    return "\n".join(lines)


def generate_section(section: dict) -> str:
    """Generate markdown section from template section definition."""
    lines = []

    title = section.get("title", "")
    section_id = section.get("id", "")

    # Add heading (titles already include ##)
    if title.startswith("##"):
        lines.append(title)
    else:
        lines.append(f"## {title}")
    lines.append("")

    # Add placeholder content based on section type
    if section_id == "instructions":
        lines.append("{{task description}}")
        lines.append("")
    elif section_id == "variables":
        lines.append("### Dynamic Variables")
        lines.append("")
        lines.append("TARGET: $ARGUMENTS")
        lines.append("")
    elif section_id == "context":
        lines.append("{{runtime context injection}}")
        lines.append("")
    elif section_id == "workflow":
        lines.append("### Phase 1: {{Phase Name}}")
        lines.append("")
        lines.append("{{phase description}}")
        lines.append("")
        lines.append("Steps:")
        lines.append("1. {{step}}")
        lines.append("2. {{step}}")
        lines.append("")
    else:
        lines.append("{{content}}")
        lines.append("")

    return "\n".join(lines)


def generate_skeleton(
    template: dict, name: str, agent: str, sections_to_include: list
) -> str:
    """Generate the full skeleton from the template."""
    parts = []

    # Frontmatter
    include_args = "variables" in sections_to_include
    parts.append(generate_frontmatter(template, name, agent, include_args))
    parts.append("")

    # Get sections from template
    all_sections = template["command_template"].get("sections", [])

    # Generate requested sections
    for section in all_sections:
        section_id = section.get("id", "")

        if section_id in sections_to_include:
            parts.append(generate_section(section))

    return "\n".join(parts)


def scaffold_command(
    name: str, path: str, agent: str, template_variant: str = "minimal"
) -> None:
    """Create a command skeleton file from YAML template."""

    # Load template
    template = load_template()

    # Determine which sections to include based on variant
    if template_variant == "minimal":
        sections = ["instructions"]
    elif template_variant == "with-args":
        sections = ["variables", "instructions"]
    elif template_variant == "with-workflow":
        sections = ["instructions", "workflow"]
    elif template_variant == "full":
        sections = ["variables", "context", "instructions", "workflow"]
    else:
        sections = ["instructions"]

    # Generate skeleton
    content = generate_skeleton(template, name, agent, sections)

    # Ensure path exists
    path_obj = Path(path).expanduser()
    path_obj.mkdir(parents=True, exist_ok=True)

    # Create file path
    filename = f"{name}.md"
    filepath = path_obj / filename

    # Check if file exists
    if filepath.exists():
        print(f"Error: {filepath} already exists", file=sys.stderr)
        sys.exit(1)

    # Write file
    filepath.write_text(content)
    print(f"Created command skeleton: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new command file from YAML template"
    )
    parser.add_argument("name", help="Command name in kebab-case (e.g., 'run-tests')")
    parser.add_argument(
        "--path", required=True, help="Directory to create the command file"
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent that executes this command (e.g., 'build', 'prompter')",
    )
    parser.add_argument(
        "--template",
        choices=["minimal", "with-args", "with-workflow", "full"],
        default="minimal",
        help="Template variant: minimal, with-args, with-workflow, or full (default: minimal)",
    )

    args = parser.parse_args()
    scaffold_command(args.name, args.path, args.agent, args.template)


if __name__ == "__main__":
    main()
