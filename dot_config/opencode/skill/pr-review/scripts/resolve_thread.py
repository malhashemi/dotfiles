# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Resolve a review thread by its GraphQL ID.

Usage: uv run resolve_thread.py <THREAD_ID>
Output: JSON with resolution confirmation
"""

import json
import subprocess
import sys


MUTATION = """
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread {
      id
      isResolved
    }
  }
}
"""


def run_gh_graphql(query: str, variables: dict) -> dict:
    """Run gh GraphQL mutation and return output."""
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-f", f"{key}={value}"])

    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def resolve_thread(thread_id: str) -> dict:
    """Resolve a review thread."""
    data = run_gh_graphql(MUTATION, {"threadId": thread_id})
    return data["data"]["resolveReviewThread"]["thread"]


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run resolve_thread.py <THREAD_ID>", file=sys.stderr)
        sys.exit(1)

    thread_id = sys.argv[1]

    try:
        result = resolve_thread(thread_id)
        print(json.dumps(result, indent=2))
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
