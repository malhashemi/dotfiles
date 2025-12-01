# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Request re-review by posting a summary comment tagging @gemini-code-assist.

Usage: uv run request_review.py <OWNER> <REPO> <PR_NUMBER> <SUMMARY_BODY>
Output: Comment URL
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
    if len(sys.argv) != 5:
        print(
            "Usage: uv run request_review.py <OWNER> <REPO> <PR_NUMBER> <SUMMARY_BODY>",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo, pr_number, body = sys.argv[1:5]

    try:
        result = request_review(owner, repo, pr_number, body)
        print(result)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
