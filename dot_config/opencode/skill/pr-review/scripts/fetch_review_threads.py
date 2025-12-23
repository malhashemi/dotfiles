# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Fetch all review threads with resolution status using GraphQL.

Usage: uv run fetch_review_threads.py <OWNER> <REPO> <PR_NUMBER>
Output: JSON with thread IDs, resolution status, and first comment
"""

import json
import subprocess
import sys


GRAPHQL_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 1) {
            nodes {
              id
              databaseId
              body
              author {
                login
              }
              createdAt
            }
          }
        }
      }
    }
  }
}
"""


def run_gh_graphql(query: str, variables: dict) -> dict:
    """Run gh GraphQL query and return output."""
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if isinstance(value, int):
            args.extend(["-F", f"{key}={value}"])
        else:
            args.extend(["-f", f"{key}={value}"])

    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def fetch_threads(owner: str, repo: str, pr_number: int) -> list[dict]:
    """Fetch review threads with resolution status."""
    variables = {"owner": owner, "repo": repo, "pr": pr_number}
    data = run_gh_graphql(GRAPHQL_QUERY, variables)

    threads = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]

    # Transform to simplified format
    return [
        {
            "thread_id": t["id"],
            "is_resolved": t["isResolved"],
            "is_outdated": t["isOutdated"],
            "path": t["path"],
            "line": t["line"],
            "first_comment": t["comments"]["nodes"][0]
            if t["comments"]["nodes"]
            else None,
        }
        for t in threads
    ]


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: uv run fetch_review_threads.py <OWNER> <REPO> <PR_NUMBER>",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo, pr_number = sys.argv[1], sys.argv[2], int(sys.argv[3])

    try:
        threads = fetch_threads(owner, repo, pr_number)
        print(json.dumps(threads, indent=2))
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
