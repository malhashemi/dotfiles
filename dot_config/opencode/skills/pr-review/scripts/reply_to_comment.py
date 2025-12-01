# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Reply to a specific review comment.

Usage: uv run reply_to_comment.py <OWNER> <REPO> <PR_NUMBER> <COMMENT_ID> <BODY>
Output: JSON response from GitHub API
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


def reply_to_comment(
    owner: str, repo: str, pr_number: str, comment_id: str, body: str
) -> dict:
    """Reply to a specific review comment."""
    endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies"
    output = run_gh(["api", endpoint, "-f", f"body={body}"])
    return json.loads(output)


def main():
    if len(sys.argv) != 6:
        print(
            "Usage: uv run reply_to_comment.py <OWNER> <REPO> <PR_NUMBER> <COMMENT_ID> <BODY>",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo, pr_number, comment_id, body = sys.argv[1:6]

    try:
        result = reply_to_comment(owner, repo, pr_number, comment_id, body)
        print(json.dumps(result, indent=2))
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
