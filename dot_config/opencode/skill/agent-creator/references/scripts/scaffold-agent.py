# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
dubstack Agent Scaffolding Script

Creates the directory structure and empty file shells for a new dubstack
agent under .vera/agents/{agent_id}/. The agent-creator skill fills the
files during the conversation — this script just creates the skeleton.

Layout produced (primary agent):
    .vera/agents/{agent_id}/
        agent.yaml          (empty — skill writes the artifact descriptor)
        frontmatter.md      (empty — skill writes the YAML frontmatter)
        persona.md          (empty — skill writes the <persona> block)
        menu.md             (empty — skill writes the <menu> block)

Layout produced (subagent):
    .vera/agents/{agent_id}/
        agent.yaml          (empty)
        frontmatter.md      (empty)
        persona.md          (empty — SAME 4-tag shape as primary)
        instructions.md     (empty — <input-expectations> + <workflow>)

Usage:
    uv run scaffold-agent.py <agent_id> [--subagent]

Examples:
    uv run scaffold-agent.py architect
    uv run scaffold-agent.py codebase-validator --subagent
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def find_vera_agents_dir() -> Path:
    """Locate the .vera/agents/ directory by walking up from CWD."""

    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        vera = candidate / ".vera"
        if vera.is_dir() and (vera / "vera.config.yaml").exists():
            return vera / "agents"
    # Fallback: assume we're at the project root and create .vera/agents/
    return cwd / ".vera" / "agents"


def scaffold_agent(agent_id: str, mode: str) -> None:
    """Create directory + empty file shells for a new agent."""

    if not agent_id:
        print("Error: agent_id is required", file=sys.stderr)
        sys.exit(1)

    if not agent_id.islower() or " " in agent_id:
        print(
            f"Error: agent_id must be lowercase with no spaces: '{agent_id}'",
            file=sys.stderr,
        )
        sys.exit(1)

    if agent_id.startswith("-") or agent_id.endswith("-"):
        print(
            f"Error: agent_id must not start or end with hyphen: '{agent_id}'",
            file=sys.stderr,
        )
        sys.exit(1)

    agents_dir = find_vera_agents_dir()
    agent_dir = agents_dir / agent_id

    if agent_dir.exists():
        print(
            f"Error: Agent directory already exists at {agent_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    agent_dir.mkdir(parents=True, exist_ok=True)

    # Always-present files
    (agent_dir / "agent.yaml").touch()
    (agent_dir / "frontmatter.md").touch()

    # Mode-specific shells
    if mode == "primary":
        (agent_dir / "persona.md").touch()
        (agent_dir / "menu.md").touch()
        shells = ["agent.yaml", "frontmatter.md", "persona.md", "menu.md"]
    else:  # subagent
        (agent_dir / "instructions.md").touch()
        shells = ["agent.yaml", "frontmatter.md", "instructions.md"]

    print(f"Scaffolded agent directory: {agent_dir}/")
    for shell in shells:
        print(f"  - {shell} (empty; agent-creator skill will fill)")
    print()
    print("Next: the agent-creator skill writes content into these files.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new dubstack agent source directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "agent_id",
        help="Agent ID (lowercase, hyphens; becomes the directory name).",
    )
    parser.add_argument(
        "--subagent",
        action="store_true",
        help="Scaffold for a subagent (instructions.md instead of persona.md + menu.md).",
    )
    args = parser.parse_args()

    mode = "subagent" if args.subagent else "primary"
    scaffold_agent(args.agent_id, mode)


if __name__ == "__main__":
    main()
