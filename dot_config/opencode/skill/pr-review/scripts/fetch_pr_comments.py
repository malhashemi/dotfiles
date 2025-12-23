# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Fetch all review comments for a PR with full metadata.

Usage: uv run fetch_pr_comments.py <OWNER> <REPO> <PR_NUMBER>
Output: JSON array of comments with id, path, line, body, author
"""

import json
import subprocess
import sys


def run_gh(args: list[str]) -> str:
    """Run gh CLI command and return output."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def fetch_comments(owner: str, repo: str, pr_number: str) -> list[dict]:
    """Fetch code review comments (inline comments on specific lines)."""
    endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/comments"
    output = run_gh(["api", endpoint])
    comments = json.loads(output)

    # Transform to simplified format
    return [
        {
            "id": c["id"],
            "path": c["path"],
            "line": c.get("line"),
            "original_line": c.get("original_line"),
            "body": c["body"],
            "author": c["user"]["login"],
            "created_at": c["created_at"],
            "in_reply_to_id": c.get("in_reply_to_id"),
            "html_url": c["html_url"],
        }
        for c in comments
    ]


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: uv run fetch_pr_comments.py <OWNER> <REPO> <PR_NUMBER>",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo, pr_number = sys.argv[1:4]

    try:
        comments = fetch_comments(owner, repo, pr_number)
        print(json.dumps(comments, indent=2))
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
