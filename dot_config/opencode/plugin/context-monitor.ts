import type { Plugin } from "@opencode-ai/plugin";

const CONTEXT_LIMIT = 1000000; // Claude's context window
const THRESHOLD = 0.6; // 60%

export const contextMonitor: Plugin = async ({ client }) => {
  // Track which sessions to monitor (only children with parentID)
  const monitoredSessions = new Set<string>();
  const warned = new Set<string>();

  return {
    async event({ event }) {
      // =============================================
      // STEP 1: Register child sessions at creation
      // =============================================
      if (event.type === "session.created") {
        const session = event.properties.info;

        if (session.parentID) {
          // Child session - activate monitoring
          monitoredSessions.add(session.id);
        }
        // Root sessions (no parentID) - skip, human is in control
        return;
      }

      // =============================================
      // STEP 2: Track tokens only for monitored sessions
      // =============================================
      if (event.type === "message.part.updated") {
        const part = event.properties.part;
        const sessionID = part.sessionID;

        // Skip if not a monitored session
        if (!monitoredSessions.has(sessionID)) return;

        // Skip if not a step-finish part (contains token info)
        if (part.type !== "step-finish") return;

        // Calculate token usage
        const tokens =
          part.tokens.input + part.tokens.output + part.tokens.cache.read;
        const usage = tokens / CONTEXT_LIMIT;

        // Inject warning at threshold (only once per session)
        if (usage >= THRESHOLD && !warned.has(sessionID)) {
          warned.add(sessionID);

          await client.session.prompt({
            path: { id: sessionID },
            body: {
              noReply: true,
              parts: [
                {
                  type: "text",
                  text: `<critical-system-reminder priority="MAX">
STOP IMMEDIATELY. Context utilization has crossed 60% — you are entering the unreliable zone where hallucinations increase and tool calls become malformed.

MANDATORY ESCAPE-HATCH PROTOCOL:
1. Do NOT continue the current task.
2. Do NOT commit any in-progress work.
3. Discard uncommitted changes: \`git checkout .\`
4. Return to the parent agent with this exact signal:

NEEDS_DECOMPOSITION
Completed: [what you finished and committed before this point]
Remaining: [what's left to do]
Suggested sub-phases: [if you can identify natural break points, list them]

The parent agent will decompose the work and dispatch fresh subagents. This is the correct, expected behavior — not a failure. Your job is to surface accurately, not to push through.
</critical-system-reminder>`,
                },
              ],
            },
          });
        }
        return;
      }

      // =============================================
      // STEP 3: Cleanup on session end
      // =============================================
      if (event.type === "session.deleted") {
        const sessionID = event.properties.info.id;
        monitoredSessions.delete(sessionID);
        warned.delete(sessionID);
        return;
      }

      // =============================================
      // STEP 4: Reset warning on idle (for continuation)
      // =============================================
      if (event.type === "session.idle") {
        const sessionID = event.properties.sessionID;
        warned.delete(sessionID); // Allow re-warning if session continues
        return;
      }
    },
  };
};

export default contextMonitor;
