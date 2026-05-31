import type { Plugin, PluginInput } from "@opencode-ai/plugin"
import { existsSync } from "node:fs"

// ---------------------------------------------------------------------------
// cmux-context — live context-window gauge in the cmux workspace progress bar.
//
// Surfaces how full the *root* (human) session's context window is, using
// cmux's dedicated `set-progress` widget (separate from the status pills that
// cmux.ts manages). Updates once per assistant step; clears when the session
// is deleted. No-op outside a cmux workspace.
//
// Source signal mirrors context-monitor.ts: the per-step token usage reported
// on `message.part.updated` / `step-finish` parts.
// ---------------------------------------------------------------------------

type Shell = PluginInput["$"]

// Approx context window for the active model. Matches context-monitor.ts.
// Tune if you switch to a model with a different window.
const CONTEXT_LIMIT = 1_000_000

const CMUX = ((): string => {
  const fromEnv = process.env.CMUX_BUNDLED_CLI_PATH
  if (fromEnv && existsSync(fromEnv)) return fromEnv
  return "cmux"
})()

function isInCmux(): boolean {
  return (
    existsSync(process.env.CMUX_SOCKET_PATH ?? "/tmp/cmux.sock") ||
    !!process.env.CMUX_WORKSPACE_ID
  )
}

async function setProgress($: Shell, fraction: number, label: string): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} set-progress ${fraction.toFixed(4)} --label ${label}`
      .quiet()
      .nothrow()
  } catch {
    // swallow errors silently
  }
}

async function clearProgress($: Shell): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} clear-progress`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

// Dedicated status key for the context gauge. Distinct from the "opencode"
// key that cmux.ts drives (working/waiting/question), so the two coexist.
const STATUS_KEY = "ctx"

// Green (healthy) -> amber (filling, >=60%) -> red (danger, >=85%).
function colorForPct(pct: number): string {
  if (pct >= 85) return "#ef4444" // red
  if (pct >= 60) return "#f59e0b" // amber
  return "#22c55e" // green
}

async function setStatus(
  $: Shell,
  text: string,
  color: string,
): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} set-status ${STATUS_KEY} ${text} --icon gauge --color ${color}`
      .quiet()
      .nothrow()
  } catch {
    // swallow errors silently
  }
}

async function clearStatus($: Shell): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} clear-status ${STATUS_KEY}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

export const cmuxContext: Plugin = async ({ client, $ }) => {
  // sessionID -> isRoot (no parentID). Populated on session.created and
  // lazily via session.get for sessions that predate plugin load (resumes).
  const isRoot = new Map<string, boolean>()

  async function resolveIsRoot(sessionID: string): Promise<boolean> {
    const cached = isRoot.get(sessionID)
    if (cached !== undefined) return cached
    try {
      const result = await client.session.get({ path: { id: sessionID } })
      const root = !result.data?.parentID
      isRoot.set(sessionID, root)
      return root
    } catch {
      // Unknown — assume non-root so we don't clobber the bar with a child.
      isRoot.set(sessionID, false)
      return false
    }
  }

  return {
    async event({ event }) {
      const e = event as any

      if (e.type === "session.created") {
        const info = e.properties?.info
        if (info?.id) isRoot.set(info.id, !info.parentID)
        return
      }

      if (e.type === "session.deleted") {
        const id = e.properties?.info?.id
        if (id) {
          if (isRoot.get(id)) {
            await clearProgress($)
            await clearStatus($)
          }
          isRoot.delete(id)
        }
        return
      }

      if (e.type === "message.part.updated") {
        const part = e.properties?.part
        if (!part || part.type !== "step-finish") return

        const sessionID = part.sessionID
        if (!sessionID) return
        if (!(await resolveIsRoot(sessionID))) return

        const t = part.tokens ?? {}
        const used =
          (t.input ?? 0) + (t.output ?? 0) + (t.cache?.read ?? 0)
        if (used <= 0) return

        const fraction = Math.max(0, Math.min(1, used / CONTEXT_LIMIT))
        const pct = Math.round(fraction * 100)
        const tokK = Math.round(used / 1000)
        await setProgress($, fraction, `ctx ${pct}% (${tokK}k)`)
        await setStatus($, `ctx ${pct}%`, colorForPct(pct))
        return
      }
    },
  }
}

export default cmuxContext
