# Assessment File Format

Write assessment to: `thoughts/shared/pr-reviews/{{pr_number}}/assessment.md`

## Template

```markdown
# PR #{{pr_number}} Review Assessment

## Metadata

- **PR**: #{{pr_number}} - {{title}}
- **Branch**: {{branch}}
- **Assessed by**: Researcher agent
- **Timestamp**: {{ISO timestamp}}
- **Iteration**: {{n}} of max 5

## Summary

| Category | Count |
|----------|-------|
| Address | {{n}} |
| Decline | {{n}} |
| Defer | {{n}} |
| **Total** | {{n}} |

## Thread Analysis

### Thread 1: `{{path}}:{{line}}`

**Thread ID**: `{{thread_id}}`
**Comment ID**: `{{comment_id}}`

**Gemini's Concern**:
> {{Quoted comment from Gemini}}

**Code Analysis**:
{{What we found by reading the actual code. MUST include evidence that code was read.}}

**Decision**: Address | Decline | Defer

**Rationale**:
{{Detailed reasoning for the decision}}

**Implementation Notes** (if Address):
{{Specific changes needed}}

---

### Thread 2: `{{path}}:{{line}}`

{{Same format...}}

---

## Verification Checklist

- [ ] All threads analyzed
- [ ] Code was read for each thread (evidence provided)
- [ ] Decisions are justified with rationale
- [ ] Implementation notes provided for Address items
```
