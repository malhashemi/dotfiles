# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Scaffold a new agent file by reading the YAML template.

Usage: uv run scaffold_agent.py <type> <name> --path <path>

Arguments:
    type    Agent type: 'primary' or 'subagent'
    name    Agent name in kebab-case (e.g., 'my-agent')
    --path  Directory to create the agent file

Output: Creates a markdown file with the agent skeleton structure derived from the YAML template.

Examples:
    uv run scaffold_agent.py primary code-reviewer --path .opencode/agent
    uv run scaffold_agent.py subagent pattern-finder --path .opencode/agent
"""

import argparse
import sys
from pathlib import Path
import yaml


def load_template(template_type: str) -> dict:
    """Load the YAML template for the given agent type."""
    script_dir = Path(__file__).parent
    references_dir = script_dir.parent / "references"

    template_file = references_dir / f"{template_type}.yaml"

    if not template_file.exists():
        print(f"Error: Template file not found: {template_file}", file=sys.stderr)
        sys.exit(1)

    with open(template_file) as f:
        return yaml.safe_load(f)


def generate_frontmatter(template: dict, name: str, agent_type: str) -> str:
    """Generate frontmatter from template."""
    if agent_type == "primary":
        root_key = "primary_agent_template"
    else:
        root_key = "subagent_template"

    frontmatter = template[root_key]["frontmatter"]

    lines = ["---"]

    # Add required fields
    for key, value in frontmatter.get("required", {}).items():
        if key == "mode":
            lines.append(f"mode: {agent_type}")
        elif key == "description":
            lines.append(f'description: "TODO: Add description for {name}"')
        elif key == "tools":
            lines.append("tools:")
            # Default tools based on type
            if agent_type == "primary":
                default_tools = {
                    "bash": False,
                    "edit": False,
                    "write": False,
                    "read": True,
                    "grep": True,
                    "glob": True,
                    "list": True,
                    "todowrite": False,
                    "todoread": False,
                    "task": False,
                }
            else:
                default_tools = {"read": True, "grep": True, "glob": True, "list": True}
            for tool, enabled in default_tools.items():
                lines.append(f"  {tool}: {str(enabled).lower()}")

    lines.append("---")
    return "\n".join(lines)


def generate_section(section: dict, level: int = 2) -> str:
    """Generate markdown section from template section definition."""
    lines = []

    title = section.get("title", "")
    # Replace template placeholders with generic text
    title = title.replace("{{N}}", "1")
    title = title.replace("{{DESCRIPTIVE_NAME}}", "PHASE_NAME")
    title = title.replace("{{type}}", "Interactive")
    title = title.replace("{{Domain}}", "Domain")
    title = title.replace("{{Domain_Specific_Title}}", "Domain Knowledge")

    # Add heading
    heading = "#" * level
    lines.append(f"{heading} {title}")
    lines.append("")

    # Add placeholder based on type
    section_type = section.get("type", "text")

    if section_type == "bullet-list":
        lines.append("- **{{Role}}**: {{description}}")
        lines.append("")
    elif section_type == "numbered-list":
        lines.append("1. {{Step}}")
        lines.append("2. {{Step}}")
        lines.append("")
    elif section_type == "checklist":
        lines.append("[ ] {{criterion}}")
        lines.append("")
    elif section_type == "template-text":
        template = section.get("template", "{{content}}")
        # Simplify template placeholders
        lines.append(template.strip())
        lines.append("")
    else:
        lines.append("{{content}}")
        lines.append("")

    # Recurse into subsections
    for subsection in section.get("sections", []):
        lines.append(generate_section(subsection, level + 1))

    return "\n".join(lines)


def generate_skeleton(template: dict, name: str, agent_type: str) -> str:
    """Generate the full skeleton from the template."""
    if agent_type == "primary":
        root_key = "primary_agent_template"
    else:
        root_key = "subagent_template"

    parts = []

    # Frontmatter
    parts.append(generate_frontmatter(template, name, agent_type))
    parts.append("")

    # Sections
    sections = template[root_key].get("sections", [])
    for section in sections:
        # Skip optional sections for cleaner skeleton, but include key ones
        section_id = section.get("id", "")
        is_optional = section.get("optional", False)

        # Always include these even if optional
        important_sections = [
            "role-definition",
            "core-identity",
            "opening-statement",
            "core-responsibilities",
            "workflow",
            "remember",
        ]

        if is_optional and section_id not in important_sections:
            continue

        parts.append(generate_section(section))

    return "\n".join(parts)


def scaffold_agent(agent_type: str, name: str, path: str) -> None:
    """Create an agent skeleton file from YAML template."""

    # Validate type
    if agent_type not in ("primary", "subagent"):
        print(
            f"Error: type must be 'primary' or 'subagent', got '{agent_type}'",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load template
    template_name = "primary-agent" if agent_type == "primary" else "subagent"
    template = load_template(template_name)

    # Generate skeleton
    content = generate_skeleton(template, name, agent_type)

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
    print(f"Created {agent_type} agent skeleton: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new agent file from YAML template"
    )
    parser.add_argument(
        "type",
        choices=["primary", "subagent"],
        help="Agent type: 'primary' or 'subagent'",
    )
    parser.add_argument("name", help="Agent name in kebab-case (e.g., 'my-agent')")
    parser.add_argument(
        "--path", required=True, help="Directory to create the agent file"
    )

    args = parser.parse_args()
    scaffold_agent(args.type, args.name, args.path)


if __name__ == "__main__":
    main()
