# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
dubstack Skill Validation Script

Validates a dubstack skill source directory for completeness and correctness
against the vera-cli native format used by dubstack:

  Source layout (per-skill, under .vera/skills/{skill_id}/):

    Workflow skill:
      skill.yaml              — artifact descriptor (type/id/destination/file_name/includes/attachments)
      head.md                 — --- name/description --- frontmatter for OpenCode
      skill-overview.md       — <skill> XML wrapper with <overview>/<workflow>/<completion>
      references/steps/*.xml  — step files (one per workflow step)
      references/scripts/*.py — PEP 723 scripts (when needed)

    Exec skill:
      skill.yaml
      head.md
      skill-overview.md       — single-shot execution definition
      references/scripts/     — when needed

    Data skill (flat layout):
      skill.yaml
      SKILL.md                — reference material

  Shared blocks referenced via includes (live at .vera/shared/):
    shared/workflow-engine.md — required for workflow skills

Usage:
    uv run validate-skill.py <path-to-skill-directory>

Example:
    uv run validate-skill.py .vera/skills/agent-creator
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

VALID_SKILL_TYPES = {"workflow", "exec", "data"}


class ValidationError:
    """Represents a validation error."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # "error" or "warning"

    def __str__(self) -> str:
        icon = "X" if self.severity == "error" else "!"
        return f"[{icon}] [{self.field}] {self.message}"


def validate_skill_yaml(
    skill_dir: Path, errors: list[ValidationError]
) -> dict[str, Any] | None:
    """Parse and validate skill.yaml. Returns the config dict if usable."""

    config_path = skill_dir / "skill.yaml"
    if not config_path.exists():
        errors.append(
            ValidationError("skill.yaml", "File not found in skill directory")
        )
        return None

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(ValidationError("skill.yaml", f"YAML parsing error: {e}"))
        return None

    if not isinstance(config, dict):
        errors.append(
            ValidationError("skill.yaml", "Top-level must be a YAML mapping")
        )
        return None

    # ---------- Reject legacy format ----------
    if "name" in config and "id" not in config:
        errors.append(
            ValidationError(
                "skill.yaml.name",
                "Legacy format detected. Use `id:` instead of `name:` in the "
                "dubstack native format.",
            )
        )
    if "references" in config or "scripts" in config:
        errors.append(
            ValidationError(
                "skill.yaml",
                "Legacy format detected. The dubstack native format uses "
                "`attachments:` for resource directories (references/, scripts/), "
                "not separate top-level `references:` and `scripts:` fields.",
            )
        )

    # ---------- Required top-level keys ----------
    for field in ("type", "id", "file_name", "includes"):
        if field not in config:
            errors.append(
                ValidationError(
                    f"skill.yaml.{field}", f"Required field '{field}' is missing"
                )
            )
        elif config[field] is None or config[field] == "":
            errors.append(
                ValidationError(f"skill.yaml.{field}", f"Field '{field}' is empty")
            )

    # ---------- type ----------
    if config.get("type") not in {None, "skill"}:
        errors.append(
            ValidationError(
                "skill.yaml.type",
                f"Expected 'skill', got: {config['type']!r}",
            )
        )

    # ---------- id ----------
    skill_id = config.get("id")
    if isinstance(skill_id, str):
        if not skill_id.islower() or " " in skill_id:
            errors.append(
                ValidationError(
                    "skill.yaml.id",
                    "Must be lowercase with hyphens; no uppercase or spaces",
                )
            )
        if skill_id.startswith("-") or skill_id.endswith("-"):
            errors.append(
                ValidationError(
                    "skill.yaml.id",
                    "Must not start or end with hyphen",
                )
            )
        if skill_id != skill_dir.name:
            errors.append(
                ValidationError(
                    "skill.yaml.id",
                    f"id ({skill_id!r}) must match directory name "
                    f"({skill_dir.name!r})",
                )
            )

    return config


def validate_includes(
    config: dict[str, Any], skill_dir: Path, errors: list[ValidationError]
) -> None:
    """Validate the `includes:` list — each path must resolve."""

    includes = config.get("includes")
    if not isinstance(includes, list):
        errors.append(
            ValidationError("skill.yaml.includes", "Must be a list of file paths")
        )
        return

    if not includes:
        errors.append(
            ValidationError(
                "skill.yaml.includes",
                "Must list at least one include file",
            )
        )
        return

    # Resolve .vera/ root from skill_dir (we're at .vera/skills/{skill_id}/).
    vera_root = skill_dir.parent.parent

    for inc in includes:
        if not isinstance(inc, str):
            errors.append(
                ValidationError(
                    "skill.yaml.includes",
                    f"Include must be a string path; got: {inc!r}",
                )
            )
            continue

        if inc.startswith("shared/"):
            target = vera_root / inc
        else:
            target = skill_dir / inc

        if not target.exists():
            errors.append(
                ValidationError(
                    f"includes.{inc}",
                    f"Include file not found at expected path: {target}",
                )
            )


def validate_attachments(
    config: dict[str, Any], skill_dir: Path, errors: list[ValidationError]
) -> None:
    """Validate the `attachments:` list — each path must resolve."""

    attachments = config.get("attachments")
    if attachments is None:
        return

    if not isinstance(attachments, list):
        errors.append(
            ValidationError(
                "skill.yaml.attachments", "If present, must be a list of paths"
            )
        )
        return

    vera_root = skill_dir.parent.parent

    for att in attachments:
        if not isinstance(att, str):
            errors.append(
                ValidationError(
                    "skill.yaml.attachments",
                    f"Attachment must be a string path; got: {att!r}",
                )
            )
            continue

        if att.startswith("shared/"):
            target = vera_root / att.rstrip("/")
        else:
            target = skill_dir / att.rstrip("/")

        if not target.exists():
            errors.append(
                ValidationError(
                    f"attachments.{att}",
                    f"Attachment path not found: {target}",
                )
            )


def read_head_frontmatter(skill_dir: Path) -> dict[str, Any] | None:
    """Read head.md's YAML frontmatter block. Returns parsed dict or None."""

    head_path = skill_dir / "head.md"
    if not head_path.exists():
        return None

    content = head_path.read_text()
    match = FRONTMATTER_RE.match(content)
    if not match:
        return None

    try:
        parsed = yaml.safe_load(match.group("fm"))
    except yaml.YAMLError:
        return None

    return parsed if isinstance(parsed, dict) else None


def detect_skill_type(
    config: dict[str, Any], skill_dir: Path
) -> str | None:
    """Detect skill type from layout and includes."""

    # Data skill = flat SKILL.md with no skill-overview.md
    if (skill_dir / "SKILL.md").exists() and not (
        skill_dir / "skill-overview.md"
    ).exists():
        return "data"

    # Workflow vs exec — workflow includes shared/workflow-engine.md
    includes = config.get("includes", [])
    if isinstance(includes, list):
        if any(
            isinstance(inc, str) and inc.endswith("workflow-engine.md")
            for inc in includes
        ):
            return "workflow"
        if (skill_dir / "skill-overview.md").exists():
            return "exec"

    return None


def validate_per_skill_files(
    config: dict[str, Any], skill_dir: Path, errors: list[ValidationError]
) -> None:
    """Validate the per-skill body files based on detected type."""

    skill_type = detect_skill_type(config, skill_dir)

    if skill_type == "data":
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(
                ValidationError(
                    "SKILL.md",
                    "Data skills require SKILL.md (flat layout — no head.md/overview split).",
                )
            )
        return

    # Workflow or exec — both require head.md + skill-overview.md
    head_path = skill_dir / "head.md"
    if not head_path.exists():
        errors.append(
            ValidationError(
                "head.md",
                "head.md is required (provides the --- name/description --- "
                "frontmatter for OpenCode skill discovery).",
            )
        )
    else:
        fm = read_head_frontmatter(skill_dir)
        if fm is None:
            errors.append(
                ValidationError(
                    "head.md",
                    "Must begin with `---` line, contain YAML name/description, "
                    "close with another `---` line.",
                )
            )
        else:
            if not fm.get("name"):
                errors.append(
                    ValidationError(
                        "head.md.name",
                        "Required `name:` field missing or empty",
                    )
                )
            if not fm.get("description"):
                errors.append(
                    ValidationError(
                        "head.md.description",
                        "Required `description:` field missing or empty",
                    )
                )

    overview_path = skill_dir / "skill-overview.md"
    if not overview_path.exists():
        errors.append(
            ValidationError(
                "skill-overview.md",
                "skill-overview.md is required (contains the <skill> XML body).",
            )
        )
    else:
        content = overview_path.read_text()
        if "<skill" not in content:
            errors.append(
                ValidationError(
                    "skill-overview.md",
                    "Expected to contain <skill> XML wrapper",
                    "warning",
                )
            )

    if skill_type == "workflow":
        # Workflow skills should have step files under references/steps/
        steps_dir = skill_dir / "references" / "steps"
        if steps_dir.exists():
            step_files = list(steps_dir.glob("step-*.xml"))
            if not step_files:
                errors.append(
                    ValidationError(
                        "references/steps",
                        "Workflow skills should have step files (step-NN-*.xml)",
                        "warning",
                    )
                )
            else:
                # Text-based check: the workflow engine reads step files
                # loosely (templating, HTML entities allowed). Strict XML
                # parsing produces false positives. Verify the structural
                # marker is present without requiring well-formed XML.
                for step_file in step_files:
                    content = step_file.read_text()
                    if "<step-file" not in content:
                        errors.append(
                            ValidationError(
                                f"steps/{step_file.name}",
                                "Missing <step-file> root marker",
                            )
                        )


def validate_skill(skill_dir: Path) -> list[ValidationError]:
    """Validate a skill source directory and return list of errors."""

    errors: list[ValidationError] = []

    config = validate_skill_yaml(skill_dir, errors)
    if config is None:
        return errors

    validate_includes(config, skill_dir, errors)
    validate_attachments(config, skill_dir, errors)
    validate_per_skill_files(config, skill_dir, errors)

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        print("Error: Please provide path to skill directory", file=sys.stderr)
        sys.exit(1)

    skill_dir = Path(sys.argv[1])

    if not skill_dir.exists():
        print(f"Error: Directory not found: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    if not skill_dir.is_dir():
        print(f"Error: Not a directory: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    errors = validate_skill(skill_dir)

    error_count = sum(1 for e in errors if e.severity == "error")
    warning_count = sum(1 for e in errors if e.severity == "warning")

    if errors:
        print(f"\nValidation results for: {skill_dir}\n")
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
        print(f"Validation PASSED: {skill_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
