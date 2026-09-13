export const meta = {
  name: 'mixed-review',
  description: 'GPT and Grok independently review a task, then Claude verifies and reconciles their findings',
  phases: [
    { title: 'Independent reviews', detail: 'Read-only GPT and Grok perspectives' },
    { title: 'Claude verification', detail: 'Check evidence and reconcile disagreements' }
  ]
}

const task = typeof args === 'string' ? args : args?.task
if (typeof task !== 'string' || !task.trim()) {
  throw new Error('Provide the task as args: { task: "what to review" }.')
}
const effort = (value, fallback, levels) => {
  const selected = value ?? fallback
  if (!levels.includes(selected)) throw new Error('Unsupported effort: ' + selected)
  return selected
}
const commonLevels = ['low', 'medium', 'high', 'xhigh', 'max']
const openaiEffort = effort(args?.openaiEffort, 'high', commonLevels)
const grokEffort = effort(args?.grokEffort, 'high', ['low', 'medium', 'high', 'xhigh'])
const claudeEffort = args?.claudeEffort === undefined ? undefined : effort(args.claudeEffort, 'high', commonLevels)

phase('Independent reviews')
const reports = await parallel([
  () => agent(
    'Review this task using available tools. Read relevant evidence; do not modify files or send messages. Propose an approach and identify correctness risks. Return concise findings with file or source references and unresolved questions. Task: ' + task,
    { model: 'gpt-6-astra', effort: openaiEffort, label: 'OpenAI · implementation review' }
  ),
  () => agent(
    'Independently challenge this task and its likely approach. Read relevant evidence; do not modify files or send messages. Look for edge cases, hidden assumptions, and failure modes. Return concise findings with file or source references and unresolved questions. Task: ' + task,
    { model: 'grok-4.6', effort: grokEffort, label: 'Grok · independent critique' }
  )
])

if (reports.some(report => report === null)) {
  log('One or more provider workers failed. Coverage is incomplete; successful results are retained.')
}

phase('Claude verification')
const verification = await agent(
  'Verify and reconcile these independent reports against evidence. Read relevant sources, but do not modify files or send messages. Distinguish confirmed findings, disagreements, and unverified claims. Explicitly report missing workers. Recommend concrete next steps. Original task: ' + task + '\nReports: ' + JSON.stringify({ openai: reports[0], grok: reports[1] }),
  { label: 'Claude · verify and reconcile', ...(claudeEffort ? { effort: claudeEffort } : {}) }
)

return { openai: reports[0], grok: reports[1], verification, incomplete: reports.some(report => report === null) || verification === null }
