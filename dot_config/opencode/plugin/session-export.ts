import type { Plugin } from "@opencode-ai/plugin"
import { mkdirSync, writeFileSync } from "node:fs"
import { dirname } from "node:path"

export const sessionExport: Plugin = async ({ client }) => {
  const exportDir = './thoughts/shared/sessions/'

  // Build nested path by walking up the ancestry chain
  // Child: sessions/{parentID}/{sessionID}.md
  // Grandchild: sessions/{grandparentID}/{parentID}/{sessionID}.md
  async function buildSessionPath(sessionID: string, parentID?: string): Promise<string> {
    const parts: string[] = [sessionID + '.md']
    
    let currentParentID = parentID
    while (currentParentID) {
      parts.unshift(currentParentID)
      // Get the parent's parent
      try {
        const parentSession = await client.session.get({ path: { id: currentParentID } })
        currentParentID = parentSession.data?.parentID
      } catch {
        // Parent session not found, stop walking
        break
      }
    }
    
    return exportDir + parts.join('/')
  }

  return {
    async event({ event }) {
      if (event.type !== "session.idle") return

      const sessionID = event.properties.sessionID

      try {
        // Get session info
        const session = await client.session.get({ path: { id: sessionID } })

        // Issue 1 Fix: Skip root sessions (human conversations)
        // Only export child sessions spawned via Task tool
        if (!session.data?.parentID) {
          return
        }

        // Get ALL messages
        const messagesResp = await client.session.messages({ path: { id: sessionID } })
        const messages = messagesResp.data || []

        // Format as Markdown transcript
        const markdown = formatTranscript(session.data, messages)

        // Build nested path based on ancestry
        const filePath = await buildSessionPath(sessionID, session.data?.parentID)
        
        // Ensure directory exists and write file
        mkdirSync(dirname(filePath), { recursive: true })
        writeFileSync(filePath, markdown, 'utf-8')
      } catch (error) {
        // Silently ignore errors - don't disrupt session
        console.error(`[session-export] Failed to export ${sessionID}:`, error)
      }
    }
  }
}

function formatTranscript(session: any, messages: any[]): string {
  const lines: string[] = []

  // Header
  lines.push(`# Session: ${session.title || session.id}`)
  lines.push('')
  lines.push(`**Session ID**: ${session.id}`)
  lines.push(`**Created**: ${new Date(session.time.created).toISOString()}`)
  if (session.parentID) {
    lines.push(`**Parent Session**: ${session.parentID}`)
  }
  lines.push('')
  lines.push('---')
  lines.push('')

  // Messages
  for (const msg of messages) {
    const role = msg.info.role === 'user' ? 'User' : 'Assistant'
    lines.push(`## ${role}`)
    lines.push('')

    for (const part of msg.parts || []) {
      // Issue 2 Fix: Handle correct SDK part types
      
      if (part.type === 'text') {
        // Skip synthetic/system-injected text
        if (part.synthetic) continue
        lines.push(part.text)
        lines.push('')
      } else if (part.type === 'reasoning') {
        // Thinking blocks (Claude's extended thinking)
        lines.push('<thinking>')
        lines.push(part.text)
        lines.push('</thinking>')
        lines.push('')
      } else if (part.type === 'tool') {
        // Tool calls with state object
        lines.push(`**Tool**: \`${part.tool}\``)
        
        // Input (args)
        if (part.state?.input) {
          lines.push('')
          lines.push('**Input**:')
          lines.push('```json')
          lines.push(JSON.stringify(part.state.input, null, 2))
          lines.push('```')
        }
        
        // Output (for completed tools)
        if (part.state?.status === 'completed' && part.state?.output) {
          lines.push('')
          lines.push('**Output**:')
          lines.push('```')
          // Truncate very long outputs
          const output = part.state.output
          if (output.length > 5000) {
            lines.push(output.substring(0, 5000) + '\n... [truncated]')
          } else {
            lines.push(output)
          }
          lines.push('```')
        }
        
        // Error (for failed tools)
        if (part.state?.status === 'error' && part.state?.error) {
          lines.push('')
          lines.push('**Error**:')
          lines.push('```')
          lines.push(part.state.error)
          lines.push('```')
        }
        
        lines.push('')
      }
      // Skip other part types: step-start, step-finish, file, agent, etc.
    }

    lines.push('---')
    lines.push('')
  }

  return lines.join('\n')
}

export default sessionExport
