#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "PyGithub>=2.1.1",
# ]
# ///

"""
GitHub Snapshot Script
Fetches all open PRs and issues with comments from a GitHub repository.

Usage:
    python3 github_snapshot.py [OPTIONS]

Examples:
    # Fetch from current repo
    python3 github_snapshot.py

    # Fetch from specific repo with verbose output
    python3 github_snapshot.py --repo owner/repo --verbose

    # Custom output directory and limit
    python3 github_snapshot.py --output-dir ./data --limit 50
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from github import Github, Auth, GithubException


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch GitHub repository snapshot (open PRs and issues)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--repo",
        type=str,
        help="Repository in format owner/repo (default: auto-detect from current directory)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory (default: thoughts/shared/github/)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of PRs/issues to fetch (default: 100)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


def get_gh_token() -> str:
    """
    Get GitHub token from gh CLI.

    Returns:
        str: GitHub authentication token

    Raises:
        SystemExit: If gh CLI not found or not authenticated
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
        token = result.stdout.strip()
        if not token:
            print("❌ Error: gh auth token returned empty string", file=sys.stderr)
            sys.exit(1)
        return token
    except subprocess.CalledProcessError as e:
        print("❌ Error: Not authenticated with GitHub CLI", file=sys.stderr)
        print("   Run: gh auth login", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: GitHub CLI (gh) not found", file=sys.stderr)
        print("   Install from: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)


def detect_current_repo() -> str:
    """
    Detect current repository using gh CLI.

    Returns:
        str: Repository in format owner/repo

    Raises:
        SystemExit: If not in a GitHub repository
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return data["nameWithOwner"]
    except subprocess.CalledProcessError:
        print("❌ Error: Not in a GitHub repository", file=sys.stderr)
        print("   Use --repo owner/repo to specify repository", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error: Failed to parse repository info: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_pull_requests(repo, limit: int, verbose: bool) -> list[Dict[str, Any]]:
    """
    Fetch open pull requests with comments.

    Args:
        repo: PyGithub repository object
        limit: Maximum number of PRs to fetch
        verbose: Enable verbose logging

    Returns:
        List of PR data dictionaries
    """
    prs_data = []

    print(f"📥 Fetching pull requests (limit: {limit})...")

    try:
        pulls = repo.get_pulls(state="open", sort="created", direction="desc")

        count = 0
        for pr in pulls:
            if count >= limit:
                break

            count += 1

            # Progress indicator
            if not verbose and count % 10 == 0:
                print(f"   ... {count} PRs fetched")

            if verbose:
                print(f"   Fetching PR #{pr.number}: {pr.title[:50]}...")

            # Fetch review comments (comments on code)
            review_comments = []
            for comment in pr.get_review_comments():
                review_comments.append(
                    {
                        "author": comment.user.login,
                        "body": comment.body,
                        "created_at": comment.created_at.isoformat(),
                        "path": comment.path,
                        "line": comment.line if hasattr(comment, "line") else None,
                    }
                )

            # Fetch issue comments (general PR comments)
            issue_comments = []
            for comment in pr.get_issue_comments():
                issue_comments.append(
                    {
                        "author": comment.user.login,
                        "body": comment.body,
                        "created_at": comment.created_at.isoformat(),
                    }
                )

            # Get labels
            labels = [label.name for label in pr.labels]

            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "url": pr.html_url,
                "body": pr.body or "",
                "labels": labels,
                "review_comments": review_comments,
                "issue_comments": issue_comments,
                "review_comments_count": len(review_comments),
                "issue_comments_count": len(issue_comments),
            }

            prs_data.append(pr_data)

        print(f"✓ Fetched {len(prs_data)} pull requests")

    except GithubException as e:
        print(f"❌ Error fetching PRs: {e.status} - {e.data}", file=sys.stderr)
        sys.exit(1)

    return prs_data


def fetch_issues(repo, limit: int, verbose: bool) -> list[Dict[str, Any]]:
    """
    Fetch open issues with comments.

    Args:
        repo: PyGithub repository object
        limit: Maximum number of issues to fetch
        verbose: Enable verbose logging

    Returns:
        List of issue data dictionaries
    """
    issues_data = []

    print(f"📥 Fetching issues (limit: {limit})...")

    try:
        issues = repo.get_issues(state="open", sort="created", direction="desc")

        count = 0
        for issue in issues:
            # Skip pull requests (they appear in issues API)
            if issue.pull_request:
                continue

            if count >= limit:
                break

            count += 1

            # Progress indicator
            if not verbose and count % 10 == 0:
                print(f"   ... {count} issues fetched")

            if verbose:
                print(f"   Fetching Issue #{issue.number}: {issue.title[:50]}...")

            # Fetch comments
            comments = []
            for comment in issue.get_comments():
                comments.append(
                    {
                        "author": comment.user.login,
                        "body": comment.body,
                        "created_at": comment.created_at.isoformat(),
                    }
                )

            # Get labels
            labels = [label.name for label in issue.labels]

            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "author": issue.user.login,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "url": issue.html_url,
                "body": issue.body or "",
                "labels": labels,
                "comments": comments,
                "comments_count": len(comments),
            }

            issues_data.append(issue_data)

        print(f"✓ Fetched {len(issues_data)} issues")

    except GithubException as e:
        print(f"❌ Error fetching issues: {e.status} - {e.data}", file=sys.stderr)
        sys.exit(1)

    return issues_data


def check_rate_limit(github_client, verbose: bool):
    """Check and warn about GitHub API rate limits."""
    try:
        rate = github_client.get_rate_limit()
        remaining = rate.resources.core.remaining
        limit = rate.resources.core.limit

        if verbose:
            print(f"⚡ API Rate Limit: {remaining}/{limit} remaining")

        if remaining < 100:
            reset_time = rate.resources.core.reset
            print(
                f"⚠️  Warning: Low API rate limit ({remaining} calls remaining)",
                file=sys.stderr,
            )
            print(f"   Resets at: {reset_time}", file=sys.stderr)

        if remaining < 50:
            print(
                "❌ Error: Insufficient API calls to complete operation",
                file=sys.stderr,
            )
            print(f"   Please wait until {rate.resources.core.reset}", file=sys.stderr)
            sys.exit(1)

    except GithubException as e:
        if verbose:
            print(f"⚠️  Warning: Could not check rate limit: {e}", file=sys.stderr)


def create_output_directory(base_dir: Optional[str]) -> Path:
    """
    Create timestamped output directory.

    Args:
        base_dir: Base directory path (default: thoughts/shared/github/)

    Returns:
        Path object for the created directory
    """
    if base_dir:
        base_path = Path(base_dir)
    else:
        base_path = Path("thoughts/shared/github")

    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    snapshot_dir = base_path / timestamp

    # Create directory structure
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "pulls").mkdir(exist_ok=True)
    (snapshot_dir / "issues").mkdir(exist_ok=True)

    return snapshot_dir


def write_metadata(
    snapshot_dir: Path,
    repo_name: str,
    prs_count: int,
    issues_count: int,
    comments_count: int,
    verbose: bool,
):
    """Write metadata JSON file."""
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "repository": repo_name,
        "snapshot_dir": str(snapshot_dir),
        "counts": {
            "pulls": prs_count,
            "issues": issues_count,
            "total_comments": comments_count,
        },
    }

    metadata_file = snapshot_dir / "_metadata.json"

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"✓ Metadata written to {metadata_file}")


def write_pr_markdown(pr_data: Dict[str, Any], output_dir: Path, verbose: bool):
    """Write a single PR to markdown file."""
    filename = output_dir / f"{pr_data['number']}.md"

    # Build content
    content = f"""---
type: pull_request
number: {pr_data["number"]}
title: "{pr_data["title"].replace('"', '\\"')}"
state: {pr_data["state"]}
author: {pr_data["author"]}
created_at: {pr_data["created_at"]}
updated_at: {pr_data["updated_at"]}
url: {pr_data["url"]}
labels: [{", ".join(pr_data["labels"])}]
---

# PR #{pr_data["number"]}: {pr_data["title"]}

**Author**: @{pr_data["author"]}
**Created**: {pr_data["created_at"]}
**Updated**: {pr_data["updated_at"]}
**Labels**: {", ".join(pr_data["labels"]) if pr_data["labels"] else "None"}

## Description

{pr_data["body"]}

## Comments ({pr_data["issue_comments_count"]})

"""

    # Add issue comments
    if pr_data["issue_comments"]:
        for comment in pr_data["issue_comments"]:
            content += f"""### @{comment["author"]} - {comment["created_at"]}

{comment["body"]}

"""
    else:
        content += "*No comments*\n\n"

    # Add review comments
    content += f"""## Review Comments ({pr_data["review_comments_count"]})

"""

    if pr_data["review_comments"]:
        for comment in pr_data["review_comments"]:
            location = (
                f"{comment['path']}:{comment['line']}"
                if comment["line"]
                else comment["path"]
            )
            content += f"""### @{comment["author"]} - {comment["created_at"]} - {location}

{comment["body"]}

"""
    else:
        content += "*No review comments*\n"

    # Write file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    if verbose:
        print(f"   Written: {filename}")


def write_issue_markdown(issue_data: Dict[str, Any], output_dir: Path, verbose: bool):
    """Write a single issue to markdown file."""
    filename = output_dir / f"{issue_data['number']}.md"

    # Build content
    content = f"""---
type: issue
number: {issue_data["number"]}
title: "{issue_data["title"].replace('"', '\\"')}"
state: {issue_data["state"]}
author: {issue_data["author"]}
created_at: {issue_data["created_at"]}
updated_at: {issue_data["updated_at"]}
url: {issue_data["url"]}
labels: [{", ".join(issue_data["labels"])}]
---

# Issue #{issue_data["number"]}: {issue_data["title"]}

**Author**: @{issue_data["author"]}
**Created**: {issue_data["created_at"]}
**Updated**: {issue_data["updated_at"]}
**Labels**: {", ".join(issue_data["labels"]) if issue_data["labels"] else "None"}

## Description

{issue_data["body"]}

## Comments ({issue_data["comments_count"]})

"""

    # Add comments
    if issue_data["comments"]:
        for comment in issue_data["comments"]:
            content += f"""### @{comment["author"]} - {comment["created_at"]}

{comment["body"]}

"""
    else:
        content += "*No comments*\n"

    # Write file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    if verbose:
        print(f"   Written: {filename}")


def write_all_output(
    snapshot_dir: Path,
    repo_name: str,
    prs_data: list[Dict[str, Any]],
    issues_data: list[Dict[str, Any]],
    verbose: bool,
):
    """Write all output files."""
    print(f"💾 Writing output to {snapshot_dir}...")

    # Calculate totals
    total_comments = sum(
        pr["review_comments_count"] + pr["issue_comments_count"] for pr in prs_data
    ) + sum(issue["comments_count"] for issue in issues_data)

    # Write metadata
    write_metadata(
        snapshot_dir,
        repo_name,
        len(prs_data),
        len(issues_data),
        total_comments,
        verbose,
    )

    # Write PRs
    if prs_data:
        print(f"   Writing {len(prs_data)} pull requests...")
        pulls_dir = snapshot_dir / "pulls"
        for pr in prs_data:
            write_pr_markdown(pr, pulls_dir, verbose)

    # Write issues
    if issues_data:
        print(f"   Writing {len(issues_data)} issues...")
        issues_dir = snapshot_dir / "issues"
        for issue in issues_data:
            write_issue_markdown(issue, issues_dir, verbose)

    print(f"✓ Output written successfully")
    print(f"📁 Snapshot location: {snapshot_dir}")


def handle_empty_results(prs_data: list, issues_data: list, verbose: bool):
    """Handle edge case of no PRs or issues found."""
    if not prs_data and not issues_data:
        print("⚠️  Warning: No open PRs or issues found", file=sys.stderr)
        if verbose:
            print("   This could mean:")
            print("   - Repository has no open items")
            print("   - Rate limit reached")
            print("   - Authentication issues")
        # Don't exit - still write metadata
        return False
    return True


def validate_repository_access(repo) -> bool:
    """Validate repository is accessible."""
    try:
        # Try to access basic repo properties
        _ = repo.name
        _ = repo.full_name
        return True
    except GithubException as e:
        if e.status == 404:
            print("❌ Error: Repository not found or not accessible", file=sys.stderr)
        elif e.status == 403:
            print(
                "❌ Error: Access forbidden - check repository permissions",
                file=sys.stderr,
            )
        else:
            print(f"❌ Error: {e.status} - {e.data}", file=sys.stderr)
        return False


def main():
    """Main execution function."""
    args = parse_arguments()

    # Determine repository
    repo_name = args.repo if args.repo else detect_current_repo()

    if args.verbose:
        print(f"🔍 Repository: {repo_name}")
        print(f"📊 Limit: {args.limit} items per type")

    print(f"✓ Target repository: {repo_name}")

    # Get authentication token
    token = get_gh_token()
    if args.verbose:
        print("✓ Authentication successful")

    # Initialize GitHub client
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth, timeout=30)  # Add timeout

        if args.verbose:
            print("✓ GitHub client initialized")

        # Check rate limits
        check_rate_limit(g, args.verbose)

        # Get repository
        repo = g.get_repo(repo_name)

        # Validate repository access
        if not validate_repository_access(repo):
            sys.exit(1)

        if args.verbose:
            print(f"✓ Repository loaded: {repo.full_name}")
            print(f"   Description: {repo.description or 'N/A'}")
            print(f"   Stars: {repo.stargazers_count}")

    except GithubException as e:
        print(f"❌ Error accessing repository: {e.status} - {e.data}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    # Fetch data
    prs_data = fetch_pull_requests(repo, args.limit, args.verbose)
    issues_data = fetch_issues(repo, args.limit, args.verbose)

    # Calculate total comments
    total_pr_comments = sum(
        pr["review_comments_count"] + pr["issue_comments_count"] for pr in prs_data
    )
    total_issue_comments = sum(issue["comments_count"] for issue in issues_data)
    total_comments = total_pr_comments + total_issue_comments

    if args.verbose:
        print(f"📊 Total PRs: {len(prs_data)}")
        print(f"📊 Total Issues: {len(issues_data)}")
        print(f"📊 Total Comments: {total_comments}")

    # Handle empty results
    has_data = handle_empty_results(prs_data, issues_data, args.verbose)

    # Close GitHub client
    g.close()

    # Create output directory
    try:
        snapshot_dir = create_output_directory(args.output_dir)

        if args.verbose:
            print(f"✓ Created output directory: {snapshot_dir}")

        # Write all output
        write_all_output(snapshot_dir, repo_name, prs_data, issues_data, args.verbose)

    except OSError as e:
        print(f"❌ Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

    print("✓ Snapshot complete")
    print(f"\n📊 Summary:")
    print(f"   Repository: {repo_name}")
    print(f"   Pull Requests: {len(prs_data)}")
    print(f"   Issues: {len(issues_data)}")
    print(f"   Total Comments: {total_comments}")
    print(f"   Location: {snapshot_dir}")
    sys.exit(0)


if __name__ == "__main__":
    main()
