# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Get PR information - auto-detects from current branch or uses provided PR number.

Usage: uv run get_pr_info.py [PR_NUMBER]
Output: JSON with PR metadata
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


def get_pr_info(pr_number: str | None = None) -> dict:
    """Get comprehensive PR information."""
    if pr_number:
        args = ["pr", "view", pr_number, "--json"]
    else:
        # Auto-detect from current branch
        args = ["pr", "view", "--json"]

    fields = [
        "number",
        "title",
        "body",
        "state",
        "url",
        "headRefName",
        "baseRefName",
        "mergeable",
        "reviewDecision",
        "statusCheckRollup",
        "author",
        "createdAt",
        "updatedAt",
    ]
    args.append(",".join(fields))

    output = run_gh(args)
    return json.loads(output)


def main():
    pr_number = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        info = get_pr_info(pr_number)
        print(json.dumps(info, indent=2))
    except subprocess.CalledProcessError as e:
        if not pr_number:
            print(
                "Error: No PR found for current branch. Please provide PR number.",
                file=sys.stderr,
            )
        else:
            print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
