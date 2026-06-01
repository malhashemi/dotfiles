# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
dubstack Agent Validation Script

Validates a dubstack agent source directory for completeness and correctness
against the vera-cli NATIVE format used by dubstack (Lock 34):

  Source layout (per-agent, under .vera/agents/{agent_id}/):
    agent.yaml       — artifact descriptor (type/id/file_name/variables/includes)
    frontmatter.md   — OpenCode YAML frontmatter as RAW markdown between --- markers
    persona.md       — <persona> XML block (primary AND subagent)
    menu.md          — <menu> XML block (primary only)
    instructions.md  — <input-expectations> + <workflow> (subagent only)

  Shared blocks referenced via includes (live at .vera/shared/):
    shared/activation.md
    shared/baseline/context-md-awareness.md
    shared/baseline/thoughts-cli-awareness.md
    shared/agent-activation.md
    shared/agent-close.md

NOT the legacy format (nested `frontmatter:` mapping in agent.yaml). This
validator rejects legacy-format agent.yaml files with a clear error.

Usage:
    uv run validate-agent.py <path-to-agent-directory>

Example:
    uv run validate-agent.py .vera/agents/ticketsmith
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(
    r"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n", re.DOTALL
)

VALID_MODES = {"primary", "subagent", "all"}


class ValidationError:
    """Represents a validation error."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # "error" or "warning"

    def __str__(self) -> str:
        icon = "X" if self.severity == "error" else "!"
        return f"[{icon}] [{self.field}] {self.message}"


def validate_agent_yaml(
    agent_dir: Path, errors: list[ValidationError]
) -> dict[str, Any] | None:
    """Parse and validate agent.yaml. Returns the config dict if usable."""

    config_path = agent_dir / "agent.yaml"
    if not config_path.exists():
        errors.append(
            ValidationError("agent.yaml", "File not found in agent directory")
        )
        return None

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(ValidationError("agent.yaml", f"YAML parsing error: {e}"))
        return None

    if not isinstance(config, dict):
        errors.append(
            ValidationError("agent.yaml", "Top-level must be a YAML mapping")
        )
        return None

    # ---------- Reject legacy format ----------
    if "frontmatter" in config:
        errors.append(
            ValidationError(
                "agent.yaml.frontmatter",
                "Legacy format detected. agent.yaml must NOT contain a "
                "nested `frontmatter:` mapping in the dubstack native format. "
                "Move frontmatter content into a separate frontmatter.md "
                "file as raw markdown between `---` markers, then list "
                "frontmatter.md in the includes array. See "
                "references/templates/agent.template.yaml for the canonical "
                "structure.",
            )
        )
    if "name" in config and "id" not in config:
        errors.append(
            ValidationError(
                "agent.yaml.name",
                "Legacy format detected. Use `id:` instead of `name:` in the "
                "dubstack native format. The field name was changed when "
                "vera-cli adopted artifact-descriptor semantics.",
            )
        )

    # ---------- Required top-level keys ----------
    for field in ("type", "id", "file_name", "includes"):
        if field not in config:
            errors.append(
                ValidationError(
                    f"agent.yaml.{field}", f"Required field '{field}' is missing"
                )
            )
        elif config[field] is None or config[field] == "":
            errors.append(
                ValidationError(f"agent.yaml.{field}", f"Field '{field}' is empty")
            )

    # ---------- type ----------
    if config.get("type") not in {None, "agent"}:
        errors.append(
            ValidationError(
                "agent.yaml.type",
                f"Expected 'agent', got: {config['type']!r}",
            )
        )

    # ---------- id ----------
    agent_id = config.get("id")
    if isinstance(agent_id, str):
        if not agent_id.islower() or " " in agent_id:
            errors.append(
                ValidationError(
                    "agent.yaml.id",
                    "Must be lowercase with hyphens; no uppercase or spaces",
                )
            )
        if agent_id.startswith("-") or agent_id.endswith("-"):
            errors.append(
                ValidationError(
                    "agent.yaml.id",
                    "Must not start or end with hyphen",
                )
            )
        if agent_id != agent_dir.name:
            errors.append(
                ValidationError(
                    "agent.yaml.id",
                    f"id ({agent_id!r}) must match directory name "
                    f"({agent_dir.name!r})",
                )
            )

    # ---------- file_name ----------
    file_name = config.get("file_name")
    if isinstance(file_name, str) and isinstance(agent_id, str):
        expected = f"{agent_id}.md"
        if file_name != expected:
            errors.append(
                ValidationError(
                    "agent.yaml.file_name",
                    f"Conventionally {expected!r}; got {file_name!r}. "
                    "Override only if intentional.",
                    "warning",
                )
            )

    return config


def validate_includes(
    config: dict[str, Any], agent_dir: Path, errors: list[ValidationError]
) -> None:
    """Validate the `includes:` list — each path must resolve."""

    includes = config.get("includes")
    if not isinstance(includes, list):
        errors.append(
            ValidationError("agent.yaml.includes", "Must be a list of file paths")
        )
        return

    if not includes:
        errors.append(
            ValidationError(
                "agent.yaml.includes",
                "Must list at least one include file",
            )
        )
        return

    # Resolve .vera/ root from agent_dir (we're at .vera/agents/{agent_id}/).
    vera_root = agent_dir.parent.parent

    for inc in includes:
        if not isinstance(inc, str):
            errors.append(
                ValidationError(
                    "agent.yaml.includes",
                    f"Include must be a string path; got: {inc!r}",
                )
            )
            continue

        if inc.startswith("shared/"):
            target = vera_root / inc
        else:
            target = agent_dir / inc

        if not target.exists():
            errors.append(
                ValidationError(
                    f"includes.{inc}",
                    f"Include file not found at expected path: {target}",
                )
            )


def validate_variables(
    config: dict[str, Any], agent_dir: Path, errors: list[ValidationError]
) -> None:
    """Validate the `variables:` block — required by mode."""

    variables = config.get("variables")

    # Detect mode from frontmatter.md (lower in this validator)
    frontmatter = read_frontmatter(agent_dir)
    mode = frontmatter.get("mode") if frontmatter else None

    if mode == "primary":
        if not isinstance(variables, dict):
            errors.append(
                ValidationError(
                    "agent.yaml.variables",
                    "Primary agents must declare a `variables:` block with "
                    "agent_id, character_name, agent_title, emoji (the four "
                    "values shared/agent-activation.md substitutes into "
                    "the <agent> open tag).",
                )
            )
            return

        expected = ("agent_id", "character_name", "agent_title", "emoji")
        for var in expected:
            if var not in variables:
                errors.append(
                    ValidationError(
                        f"variables.{var}",
                        f"Expected identity variable '{var}' missing "
                        "(referenced by shared/agent-activation.md)",
                    )
                )
            elif not variables[var]:
                errors.append(
                    ValidationError(
                        f"variables.{var}", f"Variable '{var}' is empty"
                    )
                )

        # Consistency: variables.agent_id should match top-level id
        if "agent_id" in variables and config.get("id"):
            if variables["agent_id"] != config["id"]:
                errors.append(
                    ValidationError(
                        "variables.agent_id",
                        f"variables.agent_id ({variables['agent_id']!r}) "
                        f"does not match top-level id ({config['id']!r})",
                    )
                )

    elif mode in ("subagent", "all"):
        if not isinstance(variables, dict):
            errors.append(
                ValidationError(
                    "agent.yaml.variables",
                    "Subagents must declare a `variables:` block with at "
                    "least agent_id (substituted into shared/subagent-open.md's "
                    "<subagent id=\"{{agent_id}}\"> tag).",
                )
            )
            return

        if "agent_id" not in variables:
            errors.append(
                ValidationError(
                    "variables.agent_id",
                    "Subagents must declare agent_id in variables block "
                    "(referenced by shared/subagent-open.md).",
                )
            )
        elif not variables["agent_id"]:
            errors.append(
                ValidationError(
                    "variables.agent_id", "Variable 'agent_id' is empty"
                )
            )
        elif config.get("id") and variables["agent_id"] != config["id"]:
            errors.append(
                ValidationError(
                    "variables.agent_id",
                    f"variables.agent_id ({variables['agent_id']!r}) "
                    f"does not match top-level id ({config['id']!r})",
                )
            )

    elif variables is not None and not isinstance(variables, dict):
        errors.append(
            ValidationError(
                "agent.yaml.variables",
                "If present, must be a YAML mapping",
            )
        )


def read_frontmatter(agent_dir: Path) -> dict[str, Any] | None:
    """Read frontmatter.md's YAML block. Returns parsed dict or None."""

    fm_path = agent_dir / "frontmatter.md"
    if not fm_path.exists():
        return None

    content = fm_path.read_text()
    match = FRONTMATTER_RE.match(content)
    if not match:
        return None

    try:
        parsed = yaml.safe_load(match.group("fm"))
    except yaml.YAMLError:
        return None

    return parsed if isinstance(parsed, dict) else None


def validate_frontmatter(
    agent_dir: Path, errors: list[ValidationError]
) -> dict[str, Any] | None:
    """Validate frontmatter.md exists and contains usable YAML frontmatter."""

    fm_path = agent_dir / "frontmatter.md"
    if not fm_path.exists():
        errors.append(
            ValidationError(
                "frontmatter.md",
                "File not found. Dubstack agents require a frontmatter.md "
                "file with YAML frontmatter between `---` markers.",
            )
        )
        return None

    content = fm_path.read_text()
    match = FRONTMATTER_RE.match(content)
    if not match:
        errors.append(
            ValidationError(
                "frontmatter.md",
                "Must begin with `---` line, contain YAML, then close with "
                "another `---` line. Content does not match the frontmatter "
                "block pattern.",
            )
        )
        return None

    try:
        fm = yaml.safe_load(match.group("fm"))
    except yaml.YAMLError as e:
        errors.append(
            ValidationError("frontmatter.md", f"YAML parsing error: {e}")
        )
        return None

    if not isinstance(fm, dict):
        errors.append(
            ValidationError(
                "frontmatter.md",
                "Frontmatter block must be a YAML mapping",
            )
        )
        return None

    # ---------- mode ----------
    mode = fm.get("mode")
    if mode is None:
        errors.append(
            ValidationError(
                "frontmatter.md.mode", "Required field 'mode' is missing"
            )
        )
    elif mode not in VALID_MODES:
        errors.append(
            ValidationError(
                "frontmatter.md.mode",
                f"Must be one of: {sorted(VALID_MODES)}",
            )
        )

    # ---------- description ----------
    if not fm.get("description"):
        errors.append(
            ValidationError(
                "frontmatter.md.description",
                "Required field 'description' is missing or empty",
            )
        )

    # ---------- permission map ----------
    perm = fm.get("permission")
    if not isinstance(perm, dict):
        errors.append(
            ValidationError(
                "frontmatter.md.permission",
                "Required permission map is missing or not a mapping",
            )
        )
    else:
        skill_perms = perm.get("skill")
        if mode == "primary" and not isinstance(skill_perms, dict):
            errors.append(
                ValidationError(
                    "frontmatter.md.permission.skill",
                    "Primary agents should declare permission.skill: map "
                    "(even if empty). Without it, the agent cannot invoke "
                    "any skill from its menu.",
                    "warning",
                )
            )
        elif isinstance(skill_perms, dict):
            for skill_name, value in skill_perms.items():
                if value != "allow":
                    errors.append(
                        ValidationError(
                            f"permission.skill.{skill_name}",
                            f"Expected 'allow', got: {value!r}",
                            "warning",
                        )
                    )

    return fm


def validate_per_agent_files(
    agent_dir: Path, fm: dict[str, Any] | None, errors: list[ValidationError]
) -> None:
    """Validate the per-agent body files based on mode."""

    if fm is None:
        return

    mode = fm.get("mode")

    # persona.md required for ALL modes (primary, subagent, all)
    persona_path = agent_dir / "persona.md"
    if not persona_path.exists():
        errors.append(
            ValidationError(
                "persona.md",
                "persona.md is required in the agent source directory "
                "(referenced by agent.yaml includes). Same 4-tag <persona> "
                "shape for primary and subagent.",
            )
        )
    else:
        content = persona_path.read_text()
        if "<persona>" not in content:
            errors.append(
                ValidationError(
                    "persona.md",
                    "Expected to contain <persona> XML block",
                    "warning",
                )
            )

    # Determine structural pattern: primary-style (menu.md) vs subagent-style (instructions.md).
    # mode: primary  → primary-style required
    # mode: subagent → subagent-style required
    # mode: all      → either structural pattern is valid (dual-mode primary OR dispatchable subagent)
    menu_path = agent_dir / "menu.md"
    instructions_path = agent_dir / "instructions.md"
    has_menu = menu_path.exists()
    has_instructions = instructions_path.exists()

    if mode == "all" and not (has_menu or has_instructions):
        errors.append(
            ValidationError(
                "agent.yaml",
                "mode: all requires either menu.md (primary-style, dual-mode "
                "user-facing) or instructions.md (subagent-style, dispatch-only "
                "with also-user-invokable).",
            )
        )

    is_primary_style = (mode == "primary") or (mode == "all" and has_menu)
    is_subagent_style = (mode == "subagent") or (mode == "all" and has_instructions and not has_menu)

    if is_primary_style:
        if not menu_path.exists():
            errors.append(
                ValidationError(
                    "menu.md",
                    "Primary agents require menu.md in the source "
                    "directory (referenced by agent.yaml includes).",
                )
            )
        else:
            content = menu_path.read_text()
            if "<menu>" not in content:
                errors.append(
                    ValidationError(
                        "menu.md",
                        "Expected to contain <menu> XML block",
                        "warning",
                    )
                )
    elif is_subagent_style:
        if not instructions_path.exists():
            errors.append(
                ValidationError(
                    "instructions.md",
                    "Subagents require instructions.md in the source "
                    "directory (referenced by agent.yaml includes).",
                )
            )
        else:
            content = instructions_path.read_text()
            if "<input-expectations>" not in content:
                errors.append(
                    ValidationError(
                        "instructions.md",
                        "Expected to contain <input-expectations> XML block",
                        "warning",
                    )
                )
            if "<workflow>" not in content:
                errors.append(
                    ValidationError(
                        "instructions.md",
                        "Expected to contain <workflow> XML block",
                        "warning",
                    )
                )
            if "<scope>" in content:
                errors.append(
                    ValidationError(
                        "instructions.md",
                        "Contains <scope> tag. Capability boundaries belong "
                        "in persona <principles> (stance), frontmatter "
                        "permissions (enforcement), or workflow step content "
                        "(operational).",
                    )
                )


def validate_agent(agent_dir: Path) -> list[ValidationError]:
    """Validate an agent source directory and return list of errors."""

    errors: list[ValidationError] = []

    config = validate_agent_yaml(agent_dir, errors)
    if config is None:
        return errors

    validate_includes(config, agent_dir, errors)
    fm = validate_frontmatter(agent_dir, errors)
    validate_variables(config, agent_dir, errors)
    validate_per_agent_files(agent_dir, fm, errors)

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        print("Error: Please provide path to agent directory", file=sys.stderr)
        sys.exit(1)

    agent_dir = Path(sys.argv[1])

    if not agent_dir.exists():
        print(f"Error: Directory not found: {agent_dir}", file=sys.stderr)
        sys.exit(1)

    if not agent_dir.is_dir():
        print(f"Error: Not a directory: {agent_dir}", file=sys.stderr)
        sys.exit(1)

    errors = validate_agent(agent_dir)

    error_count = sum(1 for e in errors if e.severity == "error")
    warning_count = sum(1 for e in errors if e.severity == "warning")

    if errors:
        print(f"\nValidation results for: {agent_dir}\n")
        for error in errors:
            print(f"  {error}")
        print()

    if error_count > 0:
        print(
            f"Validation FAILED: {error_count} error(s), "
            f"{warning_count} warning(s)"
        )
        sys.exit(1)
    elif warning_count > 0:
        print(f"Validation PASSED with {warning_count} warning(s)")
        sys.exit(0)
    else:
        print(f"Validation PASSED: {agent_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
