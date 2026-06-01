<extern-catalog>

<overview>
External-repository research persists to a GLOBAL store that survives
across all projects — distinct from project-local research documents.
Clones are disposable (under .extern/); research is permanent (under the
global extern store). The catalog indexes what has been studied so a
repeat question reuses prior research instead of re-cloning.
</overview>

<locations>
- Global store (persistent): `{thoughtsHome}/global/shared/extern/`
  - `catalog.md` — the research index (managed by scripts/catalog.py)
  - `repos/{org-repo}/{YYYY-MM-DD}_{topic-slug}.md` — research documents
- Workspace (disposable): `{project}/.extern/{org-repo}/` — shallow clones
The catalog.py script resolves the global store from
~/.config/thoughts/config.json automatically.
</locations>

<catalog-script>
Manage the catalog ONLY through the script — never hand-edit catalog.md.

- Check before cloning:
  `uv run {base_dir}/scripts/catalog.py search "{repo-or-topic}"`
- List all studies:
  `uv run {base_dir}/scripts/catalog.py list`
- Record a study after persisting its document:
  `uv run {base_dir}/scripts/catalog.py add-study --repo "{org/repo}" --url "{url}" --topic "{topic}" --document "repos/{org-repo}/{file}.md" --context "{why}"`

add-study auto-creates the catalog on first use and increments the
repo's study count and topic list.
</catalog-script>

<research-document>
Each study writes a document to `repos/{org-repo}/` in the global store.
This is the extern schema — NOT the project-local research document
format.

```markdown
---
date: {ISO timestamp}
repo: "{org}/{repo}"
url: "{full clone URL}"
topic: "{what was studied}"
context: "{why this was studied — the prompting need}"
project: "{the project that prompted the study}"
tags: [extern-research, {pattern-or-domain tags}]
---

# {Topic}: {Repo Name}

## Research Question

{what we set out to learn from this repo}

## Key Findings

### {Finding title}

{description with code examples and file:line references INTO THE CLONE,
e.g., `.extern/{org-repo}/src/foo.ts:42`}

## Applicable Patterns

{how these findings could transfer to our work — factual transfer
assessment (what matches, what differs), not a recommendation to adopt}

## References

- `{clone-relative file}:{line}` — {what it shows}
```
</research-document>

<clone-naming>
Derive the workspace directory as `{org}-{repo}` (lowercase, kebab-case):
- `https://github.com/facebook/react` → `facebook-react`
- `https://github.com/vercel/next.js` → `vercel-next-js`
Clone shallow unless full history is the subject of study:
`git clone --single-branch --depth 1 {url} .extern/{org-repo}/`
</clone-naming>

</extern-catalog>
