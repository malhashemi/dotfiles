import type { Plugin } from "@opencode-ai/plugin"

const CONTEXT_LIMIT = 200000  // Claude's context window
const THRESHOLD = 0.6         // 60%

export const contextMonitor: Plugin = async ({ client }) => {
  // Track which sessions to monitor (only children with parentID)
  const monitoredSessions = new Set<string>()
  const warned = new Set<string>()

  return {
    async event({ event }) {
      // =============================================
      // STEP 1: Register child sessions at creation
      // =============================================
      if (event.type === "session.created") {
        const session = event.properties.info
        
        if (session.parentID) {
          // Child session - activate monitoring
          monitoredSessions.add(session.id)
        }
        // Root sessions (no parentID) - skip, human is in control
        return
      }

      // =============================================
      // STEP 2: Track tokens only for monitored sessions
      // =============================================
      if (event.type === "message.part.updated") {
        const part = event.properties.part
        const sessionID = part.sessionID

        // Skip if not a monitored session
        if (!monitoredSessions.has(sessionID)) return

        // Skip if not a step-finish part (contains token info)
        if (part.type !== "step-finish") return

        // Calculate token usage
        const tokens = part.tokens.input + part.tokens.output + part.tokens.cache.read
        const usage = tokens / CONTEXT_LIMIT

        // Inject warning at threshold (only once per session)
        if (usage >= THRESHOLD && !warned.has(sessionID)) {
          warned.add(sessionID)

          await client.session.prompt({
            path: { id: sessionID },
            body: {
              noReply: true,
              parts: [{
                type: 'text',
                text: 'STOP IMMEDIATELY. Context threshold (60%) reached. Report back to parent agent that this execution is too big. Do not continue work.'
              }]
            }
          })
        }
        return
      }

      // =============================================
      // STEP 3: Cleanup on session end
      // =============================================
      if (event.type === "session.deleted") {
        const sessionID = event.properties.info.id
        monitoredSessions.delete(sessionID)
        warned.delete(sessionID)
        return
      }

      // =============================================
      // STEP 4: Reset warning on idle (for continuation)
      // =============================================
      if (event.type === "session.idle") {
        const sessionID = event.properties.sessionID
        warned.delete(sessionID)  // Allow re-warning if session continues
        return
      }
    }
  }
}

export default contextMonitor
