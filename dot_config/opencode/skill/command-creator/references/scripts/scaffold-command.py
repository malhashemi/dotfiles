# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Create the source files for a new VERA command, following the dubstack convention:

  .vera/commands/<id>/
    command-config.yaml   # vera build descriptor: type/id/file_name/destination/includes
    instructions.md       # YAML frontmatter (description, argument-hint, optional agent) + body

The command's IDENTITY (description, argument-hint, agent) lives in the
instructions.md frontmatter — NOT in command-config.yaml. The config is purely
the build descriptor vera-cli consumes. Global commands use `destination: "."`;
agent-specific commands use `destination: <owner_agent>` (the source dir stays
flat — agent scoping is the destination field, not a nested folder).

Usage: uv run scaffold-command.py <command_name> <command_type> [owner_agent]
  command_name: slash-command name (lowercase-hyphen); used for id, file_name, dir
  command_type: standalone | wrapper | agent-specific
  owner_agent:  agent name (required if agent-specific); sets destination + frontmatter agent
"""

import sys
import re
from pathlib import Path

COMMANDS_ROOT = Path(".vera/commands")

CONFIG_TEMPLATE = """type: command
id: {command_name}
file_name: {command_name}.md
destination: "{destination}"
includes:
  - instructions.md
"""

STANDALONE_TEMPLATE = """---
description: TODO - describe what this command does (verb-first, < 100 chars)
argument-hint: "[args]"
{agent_fm}---

<command name="{command_name}">

  <instructions>
    TODO: Describe what this command does.

    <check if="$ARGUMENTS provided">
      <action>TODO: Handle arguments</action>
    </check>
  </instructions>

  <rules>
    <rule>TODO: Add rules</rule>
  </rules>

</command>
"""

WRAPPER_TEMPLATE = """---
description: TODO - describe what this command does (verb-first, < 100 chars)
argument-hint: "[args]"
{agent_fm}---

<command name="{command_name}">

  <instructions>
    <action>Use the TODO-SKILL-NAME skill</action>
    <action>Pass $ARGUMENTS as context</action>
  </instructions>

</command>
"""


def validate_name(name: str) -> bool:
    """Validate command name format (lowercase letters, digits, single hyphens)."""
    pattern = r"^[a-z][a-z0-9-]*[a-z0-9]$|^[a-z]$"
    return bool(re.match(pattern, name)) and len(name) <= 64


def scaffold_command(
    command_name: str, command_type: str, owner_agent: str | None = None
) -> None:
    """Create the command source directory and template files."""
    if not validate_name(command_name):
        print(f"Error: Invalid command name '{command_name}'", file=sys.stderr)
        print("  - Use lowercase letters, numbers, hyphens only", file=sys.stderr)
        print("  - Cannot start or end with hyphen", file=sys.stderr)
        print("  - Max 64 characters", file=sys.stderr)
        sys.exit(1)

    valid_types = ["standalone", "wrapper", "agent-specific"]
    if command_type not in valid_types:
        print(f"Error: Invalid command type '{command_type}'", file=sys.stderr)
        print(f"  Valid types: {', '.join(valid_types)}", file=sys.stderr)
        sys.exit(1)

    # Destination + frontmatter agent: agent-specific scopes via the destination
    # field (and a frontmatter `agent:`); global commands use ".".
    if command_type == "agent-specific" or owner_agent:
        if not owner_agent:
            print(
                "Error: owner_agent required for agent-specific commands",
                file=sys.stderr,
            )
            sys.exit(1)
        destination = owner_agent
        agent_fm = f"agent: {owner_agent}\n"
    else:
        destination = "."
        agent_fm = ""

    command_dir = COMMANDS_ROOT / command_name
    command_dir.mkdir(parents=True, exist_ok=True)

    config_content = CONFIG_TEMPLATE.format(
        command_name=command_name, destination=destination
    )

    template = WRAPPER_TEMPLATE if command_type == "wrapper" else STANDALONE_TEMPLATE
    instructions_content = template.format(
        command_name=command_name, agent_fm=agent_fm
    )

    config_file = command_dir / "command-config.yaml"
    config_file.write_text(config_content)
    print(f"Created: {config_file}")

    instructions_file = command_dir / "instructions.md"
    instructions_file.write_text(instructions_content)
    print(f"Created: {instructions_file}")

    print(f"\nCommand scaffold complete: {command_dir}")
    print("Next: fill the instructions.md frontmatter (description) + body, then `vera validate`.")
    print("Remember to register the command in .vera/vera.manifest.yaml so it builds.")


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: uv run scaffold-command.py <command_name> <command_type> [owner_agent]"
        )
        print("  command_type: standalone, wrapper, or agent-specific")
        sys.exit(1)

    command_name = sys.argv[1]
    command_type = sys.argv[2]
    owner_agent = sys.argv[3] if len(sys.argv) > 3 else None

    scaffold_command(command_name, command_type, owner_agent)


if __name__ == "__main__":
    main()
