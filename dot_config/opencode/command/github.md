---
description: "Fetch and analyze all open GitHub PRs and issues with comments, generating a comprehensive status report"
agent: "build"
argument-hint: "[optional: search query or filter]"
---

## Variables

### Static Variables
GITHUB_DATA_DIR: "thoughts/shared/github/"
SNAPSHOT_SCRIPT: "~/.config/opencode/scripts/github_snapshot.py"
METADATA_FILE: "_metadata.json"
DIR_PULLS: "pulls/"
DIR_ISSUES: "issues/"
REPORT_FILENAME: "github-status-report.md"

### Analysis Agents
AGENT_THOUGHTS_LOCATOR: "thoughts-locator"
AGENT_THOUGHTS_ANALYZER: "thoughts-analyzer"

### Dynamic Variables
USER_QUERY: $ARGUMENTS
SCRIPT_VERBOSE_FLAG: ""
SCRIPT_LIMIT: "100"

## Instructions

Generate a comprehensive GitHub status report by first collecting all open PRs and issues programmatically, then analyzing them with specialized research agents.

**Two-phase execution**:
1. **Data Collection**: Invoke {{SNAPSHOT_SCRIPT}} to fetch current GitHub state into timestamped directory
2. **Analysis & Reporting**: Read the collected markdown files and generate insights

**If {{USER_QUERY}} is provided**:
- Use it as a filter or search criterion for focused analysis
- Example: "security issues", "performance PRs", "bug fixes"
- Delegate to {{AGENT_THOUGHTS_LOCATOR}} and {{AGENT_THOUGHTS_ANALYZER}} with the specific query

**If no {{USER_QUERY}}**:
- Produce a comprehensive overview of all open items
- Summarize by type (PRs vs Issues), priority, and activity level

**Output**: Save the final analysis report to the snapshot directory as {{REPORT_FILENAME}}, following the researcher header format with metadata frontmatter.

## Workflow

### Phase 1: Data Collection [Synchronous]

**1.1 Execute Snapshot Script**
1. Invoke {{SNAPSHOT_SCRIPT}} using bash tool:
   ```bash
   uv run {{SNAPSHOT_SCRIPT}} --limit {{SCRIPT_LIMIT}} {{SCRIPT_VERBOSE_FLAG}}
   ```
2. **CRITICAL**: Wait for script to complete (exit code 0)
3. Script creates timestamped directory under {{GITHUB_DATA_DIR}}

✓ Verify: Script exits successfully and creates output directory

**1.2 Handle Script Failures**
If script exits with non-zero code:
1. Check error message for authentication issues (`gh auth login`)
2. Check for rate limit warnings (wait and retry)
3. Verify repository exists and is accessible
4. Report error to user with actionable guidance

### Phase 2: Validation & Discovery [Synchronous]

**2.1 Locate Snapshot Directory**
1. List {{GITHUB_DATA_DIR}} to find latest timestamped directory
2. Set SNAPSHOT_DIR to the newly created directory path

**2.2 Read Metadata**
1. Read {{SNAPSHOT_DIR}}/{{METADATA_FILE}}
2. Extract snapshot information:
   - Repository name
   - Timestamp
   - Counts (PRs, issues, comments)
3. Store for report generation

**2.3 Validate Structure**
1. Verify {{SNAPSHOT_DIR}}/{{DIR_PULLS}} exists
2. Verify {{SNAPSHOT_DIR}}/{{DIR_ISSUES}} exists
3. List files in each directory to confirm data collected

✓ Verify: Metadata loaded, directory structure confirmed, file counts match metadata

⚠️ **CHECKPOINT**: If validation fails, report error and halt

### Phase 3: Analysis & Synthesis [Asynchronous]

**3.1 Determine Analysis Scope**

**If {{USER_QUERY}} provided**:
- Focused analysis mode
- Use query to filter relevant PRs/issues

**If no {{USER_QUERY}}**:
- Comprehensive overview mode
- Analyze all collected items

**3.2 Delegate to Analysis Agents**

Launch parallel research tasks:

1. **Locate Relevant Items**:
   - Use {{AGENT_THOUGHTS_LOCATOR}} to find all PRs and issues in {{SNAPSHOT_DIR}}
   - If {{USER_QUERY}} provided, filter results by the query
   - Request organized list by type (pulls vs issues)

2. **Deep Analysis** (if USER_QUERY provided):
   - Use {{AGENT_THOUGHTS_ANALYZER}} on items matching {{USER_QUERY}}
   - Extract key insights, priorities, and action items
   - Focus on actionable recommendations

**3.3 Read Key Files**
1. Based on agent findings, read the most relevant markdown files
2. Extract PR/issue details, comments, and context
3. **IMPORTANT**: Read files completely for accurate analysis

✓ Verify: All analysis agents complete and return findings

### Phase 4: Report Generation [Synchronous]

**4.1 Synthesize Findings**
1. Compile all data from metadata, file reads, and agent analysis
2. Organize by:
   - PRs (count, highlights, urgent items)
   - Issues (count, highlights, priority items)
   - Activity summary (most discussed, recent updates)
3. If {{USER_QUERY}} provided, focus on query-relevant insights

**4.2 Generate Report Document**
1. Create {{REPORT_FILENAME}} in {{SNAPSHOT_DIR}}
2. Use the Output Template structure (see below)
3. Include researcher-style frontmatter with metadata
4. Add GitHub permalinks where applicable

**4.3 Present Summary**
1. Display concise summary to user:
   - Total counts (PRs, issues, comments)
   - Key highlights or urgent items
   - Report location
2. Ask if user needs follow-up analysis or filtering

✓ Verify: Report saved successfully and summary presented

## Output Template

```yaml
output_specification:
  template:
    id: "github-status-report-v1"
    name: "GitHub Status Report"
    output:
      format: markdown
      path: "{{SNAPSHOT_DIR}}/{{REPORT_FILENAME}}"
      structure: hierarchical

  sections:
    - id: frontmatter
      title: "YAML Frontmatter"
      type: yaml
      required: true
      template: |
        ---
        date: [ISO timestamp from metadata]
        reporter: [User from thoughts status or git config]
        git_commit: [Current commit hash]
        branch: [Current branch]
        repository: [Repository name from metadata]
        snapshot_dir: [SNAPSHOT_DIR path]
        topic: "GitHub Status Report"
        tags: [github, status, prs, issues]
        status: complete
        last_updated: [YYYY-MM-DD]
        last_updated_by: [Reporter name]
        query: [USER_QUERY if provided, else "comprehensive"]
        ---

    - id: header
      title: "Report Header"
      type: structured
      required: true
      template: |
        # GitHub Status Report

        **Date**: [Timestamp from metadata]
        **Reporter**: [Reporter name]
        **Repository**: [Repository name]
        **Snapshot Directory**: `[SNAPSHOT_DIR]`
        **Query Filter**: [USER_QUERY or "None (comprehensive)"]

    - id: summary
      title: "Executive Summary"
      type: text
      required: true
      template: |
        ## Executive Summary

        **Total Open PRs**: [Count from metadata]
        **Total Open Issues**: [Count from metadata]
        **Total Comments**: [Count from metadata]

        [2-3 sentence high-level overview of current GitHub status]

    - id: pull-requests
      title: "Pull Requests"
      type: structured
      required: true
      template: |
        ## Pull Requests ([count])

        ### Highlights
        - [Key PR with most activity or importance]
        - [Recent or urgent PRs]

        ### All Open PRs
        - **PR #[number]**: [Title] - [Brief status, comment count]
          - Author: @[username]
          - Updated: [date]
          - Comments: [count]
          - Labels: [labels]
          - Link: [GitHub URL]

    - id: issues
      title: "Issues"
      type: structured
      required: true
      template: |
        ## Issues ([count])

        ### Highlights
        - [Key issue with most activity or importance]
        - [Recent or urgent issues]

        ### All Open Issues
        - **Issue #[number]**: [Title] - [Brief status, comment count]
          - Author: @[username]
          - Updated: [date]
          - Comments: [count]
          - Labels: [labels]
          - Link: [GitHub URL]

    - id: query-findings
      title: "Query-Specific Findings"
      type: structured
      required: false
      condition: "USER_QUERY provided"
      template: |
        ## Query-Specific Findings: "[USER_QUERY]"

        ### Matched Items
        [List of PRs/issues matching the query]

        ### Analysis
        [Insights from AGENT_THOUGHTS_ANALYZER about query-relevant items]

        ### Recommendations
        [Action items or priorities based on query focus]

    - id: activity-analysis
      title: "Activity Analysis"
      type: structured
      required: true
      template: |
        ## Activity Analysis

        ### Most Discussed
        - [PR/Issue with most comments]

        ### Recently Updated
        - [Items updated in last 24-48 hours]

        ### Stale Items
        - [Items with no recent activity, if applicable]

    - id: data-references
      title: "Data References"
      type: structured
      required: true
      template: |
        ## Data References

        **Snapshot Location**: `[SNAPSHOT_DIR]`
        **Metadata**: `[SNAPSHOT_DIR]/_metadata.json`

        ### Raw Data Files
        - Pull Requests: `[SNAPSHOT_DIR]/pulls/` ([count] files)
        - Issues: `[SNAPSHOT_DIR]/issues/` ([count] files)

    - id: next-steps
      title: "Next Steps"
      type: text
      optional: true
      template: |
        ## Suggested Next Steps

        [Optional recommendations based on analysis]
```
