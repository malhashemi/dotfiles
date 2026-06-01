# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
dubstack Skill Scaffolding Script

Creates the directory structure and empty file shells for a new dubstack
skill under .vera/skills/{skill_id}/. The skill-creator skill fills the
files during the conversation — this script just creates the skeleton.

Layout produced (workflow skill):
    .vera/skills/{skill_id}/
        skill.yaml             (empty — skill-creator writes the artifact descriptor)
        head.md                (empty — skill-creator writes the --- name/description --- block)
        skill-overview.md      (empty — skill-creator writes the <skill> XML body)
        references/steps/      (empty directory — skill-creator writes step files)
        references/scripts/    (empty directory — for PEP 723 scripts if needed)

Layout produced (exec skill):
    .vera/skills/{skill_id}/
        skill.yaml             (empty)
        head.md                (empty)
        skill-overview.md      (empty)
        references/scripts/    (empty directory)

Layout produced (data skill):
    .vera/skills/{skill_id}/
        skill.yaml             (empty)
        SKILL.md               (empty — flat layout, no head.md/overview split)

Usage:
    uv run scaffold-skill.py <skill_id> <skill_type>

Arguments:
    skill_id:   Skill name in kebab-case (e.g., "extract-knowledge")
    skill_type: One of: workflow, exec, data

Examples:
    uv run scaffold-skill.py code-grill workflow
    uv run scaffold-skill.py validate-yaml exec
    uv run scaffold-skill.py context-md-format data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def find_vera_skills_dir() -> Path:
    """Locate the .vera/skills/ directory by walking up from CWD."""

    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        vera = candidate / ".vera"
        if vera.is_dir() and (vera / "vera.config.yaml").exists():
            return vera / "skills"
    # Fallback: assume we're at the project root and create .vera/skills/
    return cwd / ".vera" / "skills"


def scaffold_skill(skill_id: str, skill_type: str) -> None:
    """Create directory + empty file shells for a new skill."""

    if not skill_id:
        print("Error: skill_id is required", file=sys.stderr)
        sys.exit(1)

    if skill_type not in ("workflow", "exec", "data"):
        print(
            f"Error: skill_type must be 'workflow', 'exec', or 'data'; got '{skill_type}'",
            file=sys.stderr,
        )
        sys.exit(1)

    if not skill_id.islower() or " " in skill_id or "_" in skill_id:
        print(
            f"Error: skill_id must be lowercase kebab-case (hyphens, no spaces or underscores): '{skill_id}'",
            file=sys.stderr,
        )
        sys.exit(1)

    if skill_id.startswith("-") or skill_id.endswith("-"):
        print(
            f"Error: skill_id must not start or end with hyphen: '{skill_id}'",
            file=sys.stderr,
        )
        sys.exit(1)

    skills_dir = find_vera_skills_dir()
    skill_dir = skills_dir / skill_id

    if skill_dir.exists():
        print(
            f"Error: Skill directory already exists at {skill_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    skill_dir.mkdir(parents=True, exist_ok=True)

    # Always-present file
    (skill_dir / "skill.yaml").touch()

    # Type-specific shells
    if skill_type == "workflow":
        (skill_dir / "head.md").touch()
        (skill_dir / "skill-overview.md").touch()
        (skill_dir / "references" / "steps").mkdir(parents=True, exist_ok=True)
        (skill_dir / "references" / "scripts").mkdir(parents=True, exist_ok=True)
        shells = [
            "skill.yaml",
            "head.md",
            "skill-overview.md",
            "references/steps/ (empty)",
            "references/scripts/ (empty)",
        ]
    elif skill_type == "exec":
        (skill_dir / "head.md").touch()
        (skill_dir / "skill-overview.md").touch()
        (skill_dir / "references" / "scripts").mkdir(parents=True, exist_ok=True)
        shells = [
            "skill.yaml",
            "head.md",
            "skill-overview.md",
            "references/scripts/ (empty)",
        ]
    else:  # data
        (skill_dir / "SKILL.md").touch()
        shells = ["skill.yaml", "SKILL.md"]

    print(f"Scaffolded skill directory: {skill_dir}/")
    for shell in shells:
        print(f"  - {shell}")
    print()
    print("Next: the skill-creator skill writes content into these files.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new dubstack skill source directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "skill_id",
        help="Skill ID (lowercase kebab-case; becomes the directory name).",
    )
    parser.add_argument(
        "skill_type",
        choices=("workflow", "exec", "data"),
        help="Skill type. workflow=multi-step interactive, exec=single-shot, data=reference material.",
    )
    args = parser.parse_args()

    scaffold_skill(args.skill_id, args.skill_type)


if __name__ == "__main__":
    main()
