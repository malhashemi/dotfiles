---
description: View and search the global extern research catalog
argument-hint: "[optional-search-term]"
agent: build
---

## Variables

### Static Variables

CATALOG_PATH: "thoughts/global/extern/catalog.md"
SKILL_DIR: "~/.config/opencode/skills/extern-researcher"

### Dynamic Variables

SEARCH_TERM: $ARGUMENTS

## Instructions

Display the global extern research catalog, optionally filtered by search term.

### If {{SEARCH_TERM}} is provided

Search the catalog for matching repos or topics:

```bash
just -f {{SKILL_DIR}}/justfile search "{{SEARCH_TERM}}"
```

Present results in a user-friendly format:
- List matching repositories
- Show topics studied for each match
- Provide links to research documents

### If no {{SEARCH_TERM}} provided

Show the full catalog overview:

```bash
just -f {{SKILL_DIR}}/justfile list
```

Also show statistics:

```bash
just -f {{SKILL_DIR}}/justfile stats
```

### Output Format

Present results clearly:

```
📚 External Repository Research Catalog

[If search term]: Showing results for "{search_term}"

{repo-name}
  URL: {url}
  Studies: {count}
  Topics: {topic1}, {topic2}
  
  Recent research:
  - {date}: {topic} → {document-link}

---
Summary: {n} repos, {m} studies
```

### Quick Actions

Remind user of available actions:
- `/extern/research [url] [question]` - Study a new repo
- `/extern/cleanup` - Remove local workspace
