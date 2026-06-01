---
description: Compact the current conversation into a portable handoff document so a fresh agent can continue the work
argument-hint: "What will the next session focus on?"
---

<command name="handoff">

  <instructions>
    Write a handoff document summarising the current conversation so a fresh agent can continue the work. When done, tell the user the path.

    Save it to the user's OS temporary directory (resolve $TMPDIR, falling back to /tmp).

    <check if="$ARGUMENTS provided">
      <action>Treat $ARGUMENTS as a description of what the next session will focus on, and tailor the document accordingly.</action>
    </check>
  </instructions>

  <rules>
    <rule>Include a "suggested skills" section naming the skills/commands the next agent should invoke.</rule>
    <rule>Do not duplicate content already captured in other artifacts (decision records, research, plans, issues, commits, diffs) — reference them by path or URL instead.</rule>
    <rule>Redact sensitive information (API keys, tokens, passwords, PII).</rule>
  </rules>

</command>
