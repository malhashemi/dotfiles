# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Validate a VERA command source directory against the dubstack convention.

A command directory contains:
  command-config.yaml  # type: command, id, file_name, destination, includes
  instructions.md      # YAML frontmatter (description, ...) + body

NOTE: this is a quick author-side pre-check. The build-authoritative validator
is `vera validate` (it understands collisions, duplicate ids, template syntax,
and the manifest). Use both.

Usage: uv run validate-command.py <command_dir>
"""

import sys
import re
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, body). frontmatter_dict is None if absent/invalid."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None, text
    return (fm if isinstance(fm, dict) else None), parts[2]


def validate_config(config_path: Path) -> tuple[dict | None, list[str]]:
    """Validate command-config.yaml (the vera build descriptor)."""
    errors: list[str] = []

    if not config_path.exists():
        return None, [f"Missing: {config_path.name}"]

    try:
        config = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        return None, [f"Invalid YAML in {config_path.name}: {e}"]

    if not config:
        return None, [f"Empty config file: {config_path.name}"]

    if config.get("type") != "command":
        errors.append('Field `type` must be "command"')

    cid = config.get("id")
    if not cid:
        errors.append("Missing required field: id")
    elif not NAME_RE.match(str(cid)):
        errors.append(f"Invalid id '{cid}' (lowercase letters, numbers, hyphens)")

    file_name = config.get("file_name")
    if not file_name:
        errors.append("Missing required field: file_name")
    elif not str(file_name).endswith(".md"):
        errors.append(f"file_name '{file_name}' should end with .md")

    if "destination" not in config:
        errors.append(
            'Missing required field: destination (use "." for a global command, '
            "or an agent name for an agent-specific one)"
        )

    includes = config.get("includes")
    if not includes:
        errors.append("Missing required field: includes")
    else:
        for include in includes:
            if not (config_path.parent / include).exists():
                errors.append(f"Include not found: {include}")

    # Identity belongs in instructions.md frontmatter, not the config.
    for legacy in ("name", "description"):
        if legacy in config:
            errors.append(
                f"`{legacy}` does not belong in command-config.yaml — "
                "it lives in the instructions.md frontmatter"
            )

    return config, errors


def validate_instructions(command_dir: Path, config: dict) -> list[str]:
    """Validate the instructions file (frontmatter description + body)."""
    errors: list[str] = []
    warnings: list[str] = []

    instructions_file = None
    for include in config.get("includes", []):
        if "instruction" in include.lower():
            instructions_file = command_dir / include
            break
    if instructions_file is None:
        for candidate in ("instructions.md", "instructions.xml"):
            if (command_dir / candidate).exists():
                instructions_file = command_dir / candidate
                break

    if instructions_file is None or not instructions_file.exists():
        return ["No instructions file found"]

    text = instructions_file.read_text()
    fm, body = split_frontmatter(text)

    if fm is None:
        errors.append(
            f"{instructions_file.name}: missing/invalid YAML frontmatter "
            "(needs at least a `description`)"
        )
    else:
        desc = fm.get("description")
        if not desc:
            errors.append(f"{instructions_file.name}: frontmatter missing `description`")
        elif str(desc).startswith("TODO"):
            errors.append(
                f"{instructions_file.name}: description not filled in (still TODO)"
            )

    if "TODO" in body:
        warnings.append(f"{instructions_file.name}: body contains TODO placeholders")

    # If the body uses the XML <command> form, sanity-check it (prose bodies are fine too).
    if "<command" in body and "<instructions" not in body:
        warnings.append(
            f"{instructions_file.name}: <command> present but no <instructions> block"
        )

    for w in warnings:
        print(f"  Warning: {w}")

    return errors


def validate_command(command_dir: Path) -> list[str]:
    """Validate a complete command directory."""
    if not command_dir.exists():
        return [f"Directory not found: {command_dir}"]
    if not command_dir.is_dir():
        return [f"Not a directory: {command_dir}"]

    print(f"Validating: {command_dir}")

    errors: list[str] = []
    config, config_errors = validate_config(command_dir / "command-config.yaml")
    errors.extend(config_errors)
    if config:
        errors.extend(validate_instructions(command_dir, config))
    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run validate-command.py <command_dir>")
        sys.exit(1)

    command_dir = Path(sys.argv[1])
    errors = validate_command(command_dir)

    if errors:
        print("\nValidation FAILED:")
        for e in errors:
            print(f"  - {e}")
        print(f"\n{len(errors)} error(s) found")
        sys.exit(1)
    print(f"\nValidation PASSED: {command_dir}")


if __name__ == "__main__":
    main()
