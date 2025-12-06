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


def find_catalog() -> Path:
    """Find the global extern catalog.

    Looks for thoughts/global/extern/catalog.md relative to common locations.
    """
    # Try relative to current directory (walk up to find thoughts/)
    current = Path.cwd()
    for _ in range(10):  # Max 10 levels up
        catalog = current / "thoughts" / "global" / "extern" / "catalog.md"
        if catalog.exists():
            return catalog
        if current.parent == current:
            break
        current = current.parent

    # Try home directory
    home_catalog = Path.home() / "thoughts" / "global" / "extern" / "catalog.md"
    if home_catalog.exists():
        return home_catalog

    raise FileNotFoundError(
        "Could not find thoughts/global/extern/catalog.md\n"
        "Please ensure the catalog exists in your thoughts directory."
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
        catalog_path = find_catalog()
    except FileNotFoundError as e:
        print(f"\n{e}\n")
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
        catalog_path = find_catalog()
    except FileNotFoundError as e:
        print(f"\n{e}\n")
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
        catalog_path = find_catalog()
    except FileNotFoundError as e:
        print(f"\n{e}\n")
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
    """Add a new study to the catalog."""
    try:
        catalog_path = find_catalog()
    except FileNotFoundError as e:
        print(f"\n{e}\n")
        return

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
