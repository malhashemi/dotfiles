# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Reply to a specific review comment.

Usage:
  uv run reply_to_comment.py <OWNER> <REPO> <PR_NUMBER> <COMMENT_ID> <BODY>
  echo "body" | uv run reply_to_comment.py <OWNER> <REPO> <PR_NUMBER> <COMMENT_ID> --stdin

Output: JSON response from GitHub API

Note: Use --stdin to pass body via stdin to avoid shell escaping issues with
backticks, $variables, and other special characters.
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
    # POST to /pulls/{pr}/comments with in_reply_to parameter
    endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/comments"
    output = run_gh(
        ["api", endpoint, "-f", f"body={body}", "-F", f"in_reply_to={comment_id}"]
    )
    return json.loads(output)


def main():
    # Support two modes:
    # 1. Body as argument: script.py OWNER REPO PR COMMENT_ID BODY
    # 2. Body from stdin:  script.py OWNER REPO PR COMMENT_ID --stdin
    if len(sys.argv) == 6 and sys.argv[5] != "--stdin":
        owner, repo, pr_number, comment_id, body = sys.argv[1:6]
    elif len(sys.argv) == 6 and sys.argv[5] == "--stdin":
        owner, repo, pr_number, comment_id = sys.argv[1:5]
        body = sys.stdin.read().strip()
    elif len(sys.argv) == 5 and not sys.stdin.isatty():
        # Piped input without --stdin flag
        owner, repo, pr_number, comment_id = sys.argv[1:5]
        body = sys.stdin.read().strip()
    else:
        print(
            "Usage: uv run reply_to_comment.py <OWNER> <REPO> <PR_NUMBER> <COMMENT_ID> <BODY>",
            file=sys.stderr,
        )
        print(
            "   or: echo 'body' | uv run reply_to_comment.py <OWNER> <REPO> <PR_NUMBER> <COMMENT_ID> --stdin",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = reply_to_comment(owner, repo, pr_number, comment_id, body)
        print(json.dumps(result, indent=2))
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
