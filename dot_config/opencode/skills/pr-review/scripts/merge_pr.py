# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Merge a PR after all reviews are addressed.

Usage: uv run merge_pr.py <PR_NUMBER> [MERGE_METHOD]
MERGE_METHOD: merge (default), squash, or rebase
Output: Merge confirmation
"""

import subprocess
import sys


VALID_METHODS = {"merge", "squash", "rebase"}


def run_gh(args: list[str]) -> str:
    """Run gh CLI command and return output."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def merge_pr(pr_number: str, method: str = "merge") -> str:
    """Merge a PR with the specified method."""
    if method not in VALID_METHODS:
        raise ValueError(f"Invalid merge method. Use: {', '.join(VALID_METHODS)}")

    return run_gh(
        [
            "pr",
            "merge",
            pr_number,
            f"--{method}",
            "--delete-branch",
        ]
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run merge_pr.py <PR_NUMBER> [MERGE_METHOD]", file=sys.stderr)
        sys.exit(1)

    pr_number = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "merge"

    try:
        result = merge_pr(pr_number, method)
        print(result)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
