#!/usr/bin/env python3
"""Manage the global extern research catalog.

This script manages a research-centric catalog stored as markdown with YAML frontmatter.
It tracks what repositories have been studied, not what is cloned.

Usage:
    python catalog.py list                    # List all research studies
    python catalog.py search <term>           # Search by repo or topic
    python catalog.py stats                   # Show catalog statistics
    python catalog.py add-study --repo "org/repo" --url "https://..." --topic "Topic" --document "path" --context "why"
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def _read_thoughts_config() -> dict[str, Any] | None:
    """Read ~/.config/thoughts/config.json to discover thoughtsHome and orgGlobal path."""
    config_path = Path.home() / ".config" / "thoughts" / "config.json"
    if not config_path.exists():
        return None
    try:
        import json

        with config_path.open() as f:
            return json.load(f).get("thoughts", {})
    except (json.JSONDecodeError, OSError):
        return None


def _catalog_in_dir(base: Path) -> Path:
    """Return the catalog path under a given extern directory."""
    return base / "catalog.md"


def _ensure_catalog(catalog_path: Path) -> Path:
    """Create the catalog and parent directories if they don't exist."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    repos_dir = catalog_path.parent / "repos"
    repos_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    initial_content = (
        "---\n"
        "type: extern-research-catalog\n"
        "version: '1.0'\n"
        f"last_updated: '{today}'\n"
        "total_repos_studied: 0\n"
        "total_studies: 0\n"
        "repos: []\n"
        "---\n"
        "\n"
        "# External Repository Research Catalog\n"
        "\n"
        "*No repositories studied yet. Use `/extern/research [url] [question]` to begin.*\n"
    )
    catalog_path.write_text(initial_content)
    print(f"  Created new catalog at {catalog_path}")
    return catalog_path


def find_catalog(create_if_missing: bool = False) -> Path:
    """Find the global extern catalog.

    Resolution order:
      1. Read ~/.config/thoughts/config.json → {thoughtsHome}/{orgGlobal.path}/shared/extern/
      2. Walk up from cwd looking for thoughts/global/org/shared/extern/ (project symlink)
      3. Fallback: ~/thoughts/global/shared/extern/ (default home path)

    If create_if_missing is True, creates the catalog at the canonical location
    (from thoughts config) when it doesn't exist.
    """
    candidates: list[Path] = []

    # 1. Canonical: read thoughts config for thoughtsHome + orgGlobal.path
    config = _read_thoughts_config()
    canonical_path: Path | None = None
    if config:
        thoughts_home = Path(config.get("thoughtsHome", "~/thoughts")).expanduser()
        org_global = config.get("orgGlobal", {})
        if org_global.get("enabled", False):
            org_path = org_global.get("path", "global")
            canonical_path = thoughts_home / org_path / "shared" / "extern"
            candidates.append(_catalog_in_dir(canonical_path))

    # 2. Walk up from cwd looking for project-level thoughts/global/org/shared/extern/
    current = Path.cwd()
    for _ in range(10):
        project_path = current / "thoughts" / "global" / "org" / "shared" / "extern"
        candidates.append(_catalog_in_dir(project_path))
        # Also check legacy path (thoughts/global/extern/) for backward compat
        legacy_path = current / "thoughts" / "global" / "extern"
        candidates.append(_catalog_in_dir(legacy_path))
        if current.parent == current:
            break
        current = current.parent

    # 3. Fallback: default home path
    candidates.append(
        _catalog_in_dir(Path.home() / "thoughts" / "global" / "shared" / "extern")
    )
    # Legacy fallback
    candidates.append(_catalog_in_dir(Path.home() / "thoughts" / "global" / "extern"))

    # Return first existing candidate
    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Not found — create if requested
    if create_if_missing:
        if canonical_path:
            return _ensure_catalog(_catalog_in_dir(canonical_path))
        # Fallback creation path
        return _ensure_catalog(
            _catalog_in_dir(Path.home() / "thoughts" / "global" / "shared" / "extern")
        )

    raise FileNotFoundError(
        "Could not find extern research catalog.\n"
        "Searched in: {thoughtsHome}/{orgGlobal.path}/shared/extern/catalog.md\n"
        "Run with create_if_missing=True or use add-study to auto-create."
    )


def parse_catalog(catalog_path: Path) -> tuple[dict[str, Any], str]:
    """Parse markdown file with YAML frontmatter.

    Returns:
        Tuple of (frontmatter_dict, markdown_body)
    """
    content = catalog_path.read_text()

    # Match YAML frontmatter between --- markers
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        raise ValueError(f"Invalid catalog format: {catalog_path}")

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)

    return frontmatter, body


def save_catalog(catalog_path: Path, frontmatter: dict[str, Any], body: str) -> None:
    """Save catalog with YAML frontmatter and markdown body."""
    yaml_content = yaml.dump(
        frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    content = f"---\n{yaml_content}---\n{body}"
    catalog_path.write_text(content)


def cmd_list(args: argparse.Namespace) -> None:
    """List all research studies."""
    try:
        catalog_path = find_catalog(create_if_missing=False)
    except FileNotFoundError:
        print("\n  No extern research catalog found.")
        print("  It will be created automatically on first add-study.\n")
        return

    frontmatter, _ = parse_catalog(catalog_path)
    repos = frontmatter.get("repos", [])

    print("\n" + "=" * 64)
    print("  External Repository Research Catalog")
    print("=" * 64)

    if not repos:
        print("\nNo repositories have been studied yet.")
        print("\nUse `/extern/research [url] [question]` to begin.\n")
        return

    for repo in repos:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "")
        study_count = repo.get("study_count", 0)
        topics = repo.get("topics", [])
        first_studied = repo.get("first_studied", "")

        print(f"\n  {name}")
        print(f"  {'─' * (len(name) + 2)}")
        print(f"  URL: {url}")
        print(f"  First studied: {first_studied}")
        print(f"  Studies: {study_count}")
        if topics:
            print(f"  Topics: {', '.join(topics)}")

    print("\n" + "=" * 64)
    total_repos = len(repos)
    total_studies = frontmatter.get("total_studies", 0)
    print(f"  Total: {total_repos} repos, {total_studies} studies")
    print("=" * 64 + "\n")


def cmd_search(args: argparse.Namespace) -> None:
    """Search catalog by repo name or topic."""
    try:
        catalog_path = find_catalog(create_if_missing=False)
    except FileNotFoundError:
        print(f"\nNo results found for '{args.term}' (no catalog exists yet)\n")
        return

    frontmatter, _ = parse_catalog(catalog_path)
    repos = frontmatter.get("repos", [])
    term = args.term.lower()

    matches = []
    for repo in repos:
        name = repo.get("name", "").lower()
        url = repo.get("url", "").lower()
        topics = [t.lower() for t in repo.get("topics", [])]

        if term in name or term in url or any(term in t for t in topics):
            matches.append(repo)

    if not matches:
        print(f"\nNo results found for '{args.term}'\n")
        return

    print(f"\n Found {len(matches)} match(es) for '{args.term}':\n")
    for repo in matches:
        name = repo.get("name", "Unknown")
        topics = repo.get("topics", [])
        print(f"  - {name}")
        if topics:
            print(f"    Topics: {', '.join(topics)}")
    print()


def cmd_stats(args: argparse.Namespace) -> None:
    """Show catalog statistics."""
    try:
        catalog_path = find_catalog(create_if_missing=False)
    except FileNotFoundError:
        print("\n  No extern research catalog found (0 repos, 0 studies).\n")
        return

    frontmatter, _ = parse_catalog(catalog_path)

    total_repos = frontmatter.get("total_repos_studied", 0)
    total_studies = frontmatter.get("total_studies", 0)
    last_updated = frontmatter.get("last_updated", "Never")
    repos = frontmatter.get("repos", [])

    # Collect all topics
    all_topics = []
    for repo in repos:
        all_topics.extend(repo.get("topics", []))
    unique_topics = set(all_topics)

    print("\n" + "=" * 40)
    print("  Extern Research Statistics")
    print("=" * 40)
    print(f"  Repositories studied: {total_repos}")
    print(f"  Total studies: {total_studies}")
    print(f"  Unique topics: {len(unique_topics)}")
    print(f"  Last updated: {last_updated}")
    print("=" * 40 + "\n")


def cmd_add_study(args: argparse.Namespace) -> None:
    """Add a new study to the catalog. Auto-creates catalog if it doesn't exist."""
    catalog_path = find_catalog(create_if_missing=True)

    frontmatter, body = parse_catalog(catalog_path)
    repos = frontmatter.get("repos", [])
    today = datetime.now().strftime("%Y-%m-%d")

    # Find or create repo entry
    repo_entry = None
    for repo in repos:
        if repo.get("name") == args.repo or repo.get("url") == args.url:
            repo_entry = repo
            break

    if repo_entry is None:
        # Create new repo entry
        repo_entry = {
            "name": args.repo,
            "url": args.url,
            "first_studied": today,
            "study_count": 0,
            "topics": [],
        }
        repos.append(repo_entry)
        frontmatter["total_repos_studied"] = (
            frontmatter.get("total_repos_studied", 0) + 1
        )

    # Update repo entry
    repo_entry["study_count"] = repo_entry.get("study_count", 0) + 1
    if args.topic not in repo_entry.get("topics", []):
        repo_entry.setdefault("topics", []).append(args.topic)

    # Update frontmatter
    frontmatter["repos"] = repos
    frontmatter["total_studies"] = frontmatter.get("total_studies", 0) + 1
    frontmatter["last_updated"] = today

    # Update markdown body - add study to repo section
    # Find or create repo section in body
    repo_slug = args.repo.lower().replace("/", "-").replace(" ", "-")
    section_header = f"### {args.repo}"

    if section_header not in body:
        # Add new section before the closing marker or at end
        new_section = f"""
{section_header}

**URL**: {args.url}  
**Studies**: 1

| Date | Topic | Document | Context |
|------|-------|----------|---------|
| {today} | {args.topic} | [{args.document}]({args.document}) | {args.context} |

"""
        # Replace the "No repositories" message if present
        if "*No repositories studied yet" in body:
            body = body.replace(
                "*No repositories studied yet. Use `/extern/research [url] [question]` to begin.*",
                new_section.strip(),
            )
        else:
            body = body.rstrip() + "\n" + new_section
    else:
        # Add row to existing table
        # Find the table after the section header
        lines = body.split("\n")
        new_lines = []
        in_section = False
        table_found = False

        for i, line in enumerate(lines):
            new_lines.append(line)
            if section_header in line:
                in_section = True
            elif (
                in_section
                and line.startswith("|")
                and "---" not in line
                and "Date" not in line
            ):
                if not table_found:
                    # Insert new row after header row
                    new_lines.append(
                        f"| {today} | {args.topic} | [{args.document}]({args.document}) | {args.context} |"
                    )
                    table_found = True
                    in_section = False

        body = "\n".join(new_lines)

        # Update study count in section
        body = re.sub(
            rf"(\*\*Studies\*\*: )(\d+)",
            lambda m: f"{m.group(1)}{repo_entry['study_count']}",
            body,
        )

    save_catalog(catalog_path, frontmatter, body)

    print(f"\n Added study to catalog:")
    print(f"  Repo: {args.repo}")
    print(f"  Topic: {args.topic}")
    print(f"  Document: {args.document}")
    print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage the global extern research catalog"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List all research studies")
    list_parser.set_defaults(func=cmd_list)

    # search command
    search_parser = subparsers.add_parser("search", help="Search by repo or topic")
    search_parser.add_argument("term", help="Search term")
    search_parser.set_defaults(func=cmd_search)

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show catalog statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # add-study command
    add_parser = subparsers.add_parser("add-study", help="Add a new study")
    add_parser.add_argument("--repo", required=True, help="Repository name (org/repo)")
    add_parser.add_argument("--url", required=True, help="Repository URL")
    add_parser.add_argument("--topic", required=True, help="Topic studied")
    add_parser.add_argument(
        "--document", required=True, help="Path to research document"
    )
    add_parser.add_argument("--context", required=True, help="Why this was studied")
    add_parser.set_defaults(func=cmd_add_study)

    args = parser.parse_args()

    if args.command is None:
        # Default to list
        args.func = cmd_list
        args.func(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
