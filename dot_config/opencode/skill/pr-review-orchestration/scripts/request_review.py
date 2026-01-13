# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Request re-review by posting a summary comment tagging @gemini-code-assist.

Usage:
  uv run request_review.py <OWNER> <REPO> <PR_NUMBER> <SUMMARY_BODY>
  echo "body" | uv run request_review.py <OWNER> <REPO> <PR_NUMBER> --stdin

Output: Comment URL

Note: Use --stdin to pass body via stdin to avoid shell escaping issues with
backticks, $variables, and other special characters.
"""

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


def request_review(owner: str, repo: str, pr_number: str, body: str) -> str:
    """Post comment tagging gemini for re-review."""
    return run_gh(
        [
            "pr",
            "comment",
            pr_number,
            "--repo",
            f"{owner}/{repo}",
            "--body",
            body,
        ]
    )


def main():
    # Support two modes:
    # 1. Body as argument: script.py OWNER REPO PR BODY
    # 2. Body from stdin:  script.py OWNER REPO PR --stdin
    if len(sys.argv) == 5 and sys.argv[4] != "--stdin":
        owner, repo, pr_number, body = sys.argv[1:5]
    elif len(sys.argv) == 5 and sys.argv[4] == "--stdin":
        owner, repo, pr_number = sys.argv[1:4]
        body = sys.stdin.read().strip()
    elif len(sys.argv) == 4 and not sys.stdin.isatty():
        # Piped input without --stdin flag
        owner, repo, pr_number = sys.argv[1:4]
        body = sys.stdin.read().strip()
    else:
        print(
            "Usage: uv run request_review.py <OWNER> <REPO> <PR_NUMBER> <SUMMARY_BODY>",
            file=sys.stderr,
        )
        print(
            "   or: echo 'body' | uv run request_review.py <OWNER> <REPO> <PR_NUMBER> --stdin",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = request_review(owner, repo, pr_number, body)
        print(result)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
