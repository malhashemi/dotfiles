import type { Plugin, PluginInput } from "@opencode-ai/plugin"
import { execSync } from "node:child_process"
import { existsSync, readFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

// ---------------------------------------------------------------------------
// Single-file build of opencode-cmux (upstream 0.2.4 + PR #13 loader fix).
//
// Upstream: https://github.com/0xCaso/opencode-cmux
// This file merges src/cmux.ts + src/index.ts into one auto-discovered plugin
// file and applies the fix from issue #12 / PR #13: the plugin module must
// expose ONLY a plugin function. The newer OpenCode loader enumerates every
// export and rejects any that is not a function ("Plugin export is not a
// function"), so LSOF_LISTEN_RE is kept as an internal (non-exported) const.
//
// Bridges OpenCode lifecycle events to cmux notifications / sidebar status /
// logs, and optionally opens cmux split panes for subagent sessions. Every
// cmux call is a no-op when not running inside a cmux workspace.
// ---------------------------------------------------------------------------

type Shell = PluginInput["$"]

// Internal — NOT exported (see header note re: PR #13).
const LSOF_LISTEN_RE = /:(\d+)\s+\(LISTEN\)/

// ===========================================================================
// cmux CLI helpers (merged from src/cmux.ts)
// ===========================================================================

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

async function getPaneLabel($: Shell): Promise<string> {
  const tmuxPane = process.env.TMUX_PANE
  if (!tmuxPane) return ""
  try {
    const result =
      await $`tmux display-message -p -t ${tmuxPane} -F '#{session_name}:#{window_index} #{pane_id}'`
        .quiet()
        .nothrow()
    if (result.exitCode === 0) {
      const text = result.stdout?.toString?.()?.trim?.()
      if (text) return `[${text}]`
    }
  } catch {}
  return `[${tmuxPane}]`
}

async function notify(
  $: Shell,
  opts: { title: string; subtitle?: string; body?: string },
): Promise<void> {
  if (!isInCmux()) return
  try {
    const prefix = await getPaneLabel($)
    const bodyParts: string[] = []
    if (opts.subtitle !== undefined) bodyParts.push(opts.subtitle)
    if (opts.body !== undefined) bodyParts.push(opts.body)
    const baseBody = bodyParts.join(" — ")
    const body = prefix
      ? baseBody
        ? `${prefix} ${baseBody}`
        : prefix
      : baseBody
    const payload = JSON.stringify({ title: opts.title, body })
    await $`${CMUX} rpc notification.create ${payload}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

async function setStatus(
  $: Shell,
  key: string,
  text: string,
  opts?: { icon?: string; color?: string },
): Promise<void> {
  if (!isInCmux()) return
  try {
    const args: string[] = [key, text]
    if (opts?.icon !== undefined) args.push("--icon", opts.icon)
    if (opts?.color !== undefined) args.push("--color", opts.color)
    await $`${CMUX} set-status ${args}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

async function clearStatus($: Shell, key: string): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} clear-status ${key}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

async function log(
  $: Shell,
  message: string,
  opts?: { level?: "info" | "success" | "error" | "warn"; source?: string },
): Promise<void> {
  if (!isInCmux()) return
  try {
    const args: string[] = []
    if (opts?.level !== undefined) {
      // cmux uses "warning" but we expose "warn" for ergonomics
      const level = opts.level === "warn" ? "warning" : opts.level
      args.push("--level", level)
    }
    if (opts?.source !== undefined) args.push("--source", opts.source)
    args.push("--", message)
    await $`${CMUX} log ${args}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

type SplitDirection = "right" | "down"

/**
 * Create a new split pane. Returns the new surface ref (e.g. "surface:5"),
 * or `null` on failure. When `fromSurface` is provided the split is created
 * relative to that surface instead of the currently focused one.
 */
async function createSplit(
  $: Shell,
  direction: SplitDirection,
  fromSurface?: string,
): Promise<string | null> {
  if (!isInCmux()) return null
  try {
    const args: string[] = [direction]
    if (fromSurface) args.push("--surface", fromSurface)
    const result = await $`${CMUX} new-split ${args}`.quiet().nothrow()
    const text = result.text().trim()
    if (!text) return null
    // Output format: "OK surface:<n> workspace:<n>"
    const match = text.match(/surface:\S+/)
    return match ? match[0] : null
  } catch {
    return null
  }
}

async function focusSurface($: Shell, surfaceId: string): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} focus-surface --surface ${surfaceId}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

async function sendToSurface(
  $: Shell,
  surfaceId: string,
  text: string,
): Promise<void> {
  if (!isInCmux()) return
  try {
    const args = ["--surface", surfaceId, text]
    await $`${CMUX} send ${args}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

async function sendKeyToSurface(
  $: Shell,
  surfaceId: string,
  key: string,
): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} send-key --surface ${surfaceId} ${key}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

async function closeSurface($: Shell, surfaceId: string): Promise<void> {
  if (!isInCmux()) return
  try {
    await $`${CMUX} close-surface --surface ${surfaceId}`.quiet().nothrow()
  } catch {
    // swallow errors silently
  }
}

// ===========================================================================
// Plugin (merged from src/index.ts)
// ===========================================================================

const plugin: Plugin = async ({ client, $ }) => {
  const pendingPermissions = new Set<string>()
  const pendingQuestions = new Set<string>()

  const originalSurfaceId = process.env.CMUX_SURFACE_ID

  // Read plugin config (once at init)
  let splitsEnabled = false
  const notifyOn: { done: boolean; permission: boolean; question: boolean; error: boolean } = {
    done: true,
    permission: true,
    question: true,
    error: true,
  }
  try {
    // Respect XDG_CONFIG_HOME, fall back to ~/.config per the XDG Base
    // Directory Specification (https://specifications.freedesktop.org/basedir-spec/).
    const configDir = process.env.XDG_CONFIG_HOME || join(homedir(), ".config")
    const configPath = join(configDir, "opencode", "opencode-cmux.json")
    const raw = readFileSync(configPath, "utf-8")
    const config = JSON.parse(raw)
    if (config.splits === true) {
      splitsEnabled = true
    }
    if (config.notifications !== undefined) {
      if (
        typeof config.notifications === "object" &&
        config.notifications !== null &&
        !Array.isArray(config.notifications)
      ) {
        const n = config.notifications as Record<string, unknown>
        for (const key of ["done", "permission", "question", "error"] as const) {
          const v = n[key]
          if (v === undefined) continue
          if (v === false) notifyOn[key] = false
          else if (v === true) notifyOn[key] = true
          else {
            console.warn(
              `[opencode-cmux] config.notifications.${key} ignored: expected boolean, got ${typeof v}`,
            )
          }
        }
      } else {
        const got = Array.isArray(config.notifications)
          ? "array"
          : typeof config.notifications
        console.warn(
          `[opencode-cmux] config.notifications ignored: expected object, got ${got}`,
        )
      }
    }
  } catch {
    // File missing, unreadable, or invalid JSON — use defaults
  }

  // Discover the actual server URL for `opencode attach`.
  //
  // The TUI does not start an HTTP server unless --port is passed.
  // Neither the serverUrl plugin input nor the SDK client baseUrl are
  // reliable — both report http://localhost:4096 regardless of the
  // actual bound port (the SDK uses in-process fetch, not HTTP).
  //
  // We use lsof to find the TCP port this process is actually listening on.
  // Returns null when no HTTP server is running (splits are skipped).
  // See: https://github.com/anomalyco/opencode/issues/9099
  let discoveredServerUrl: string | null | undefined
  function resolveServerUrl(): string | null {
    if (discoveredServerUrl !== undefined) return discoveredServerUrl

    // 1. Env var (future-proof for when anomalyco/opencode#9099 lands)
    if (process.env.OPENCODE_SERVER_URL) {
      try {
        const parsed = new URL(process.env.OPENCODE_SERVER_URL)
        if (parsed.hostname === "0.0.0.0" || parsed.hostname === "[::]") {
          parsed.hostname = "localhost"
        }
        discoveredServerUrl = parsed.toString().replace(/\/$/, "")
        return discoveredServerUrl
      } catch {}
    }

    // 2. Find the TCP port this process is listening on via lsof.
    //    Use -a to AND the -p and -iTCP filters (macOS lsof ORs by default).
    try {
      const out = execSync(
        `lsof -nP -a -p ${process.pid} -iTCP -sTCP:LISTEN 2>/dev/null`,
        { encoding: "utf-8", timeout: 3000 },
      )
      for (const line of out.split("\n")) {
        const match = line.match(LSOF_LISTEN_RE)
        if (match) {
          discoveredServerUrl = `http://localhost:${match[1]}`
          return discoveredServerUrl
        }
      }
    } catch {}

    discoveredServerUrl = null
    return null
  }

  const activeSplits = new Map<string, string>()

  // Rightmost surface in each of the 3 rows (top-right, bottom-right, bottom-left)
  // Used as split targets when adding new columns
  const rowFrontier: (string | undefined)[] = [undefined, undefined, undefined]
  let agentCount = 0

  let splitQueue = Promise.resolve<unknown>(undefined)
  function enqueueSplitOp<T>(fn: () => Promise<T>): Promise<T> {
    const result = splitQueue.then(fn, fn)
    splitQueue = result.then(
      () => {},
      () => {},
    )
    return result as Promise<T>
  }

  function resetGridState(): void {
    rowFrontier[0] = undefined
    rowFrontier[1] = undefined
    rowFrontier[2] = undefined
    agentCount = 0
  }

  function removeAndClose(sessionId: string): void {
    const surfaceId = activeSplits.get(sessionId)
    if (!surfaceId) return
    activeSplits.delete(sessionId)
    closeSurface($, surfaceId).catch(() => {})
    if (activeSplits.size === 0) {
      resetGridState()
    }
  }

  function isWaitingForInput(): boolean {
    return pendingPermissions.size > 0 || pendingQuestions.size > 0
  }

  function getPermissionRequestID(source: any): string | undefined {
    if (!source) return undefined
    const rawID = source.id ?? source.requestID ?? source.permissionID
    if (typeof rawID !== "string") return undefined
    const trimmed = rawID.trim()
    return trimmed === "" ? undefined : trimmed
  }

  function getQuestionRequestID(source: any): string | undefined {
    if (!source) return undefined
    const rawID = source.id ?? source.requestID
    if (typeof rawID !== "string") return undefined
    const trimmed = rawID.trim()
    return trimmed === "" ? undefined : trimmed
  }

  async function fetchSession(
    sessionID: string,
  ): Promise<{ title: string; parentID?: string } | null> {
    try {
      const result = await client.session.get({ path: { id: sessionID } })
      if (result.data) {
        return { title: result.data.title, parentID: result.data.parentID }
      }
      return null
    } catch {
      return null
    }
  }

  return {
    async event({ event }) {
      const e = event as any

      if (e.type === "session.created") {
        const info = e.properties.info
        if (splitsEnabled && info?.parentID) {
          const url = resolveServerUrl()
          if (url) {
            await enqueueSplitOp(async () => {
              if (activeSplits.has(info.id)) return

              let direction: SplitDirection
              let fromSurface: string | undefined
              const n = agentCount

              if (n === 0) {
                direction = "right"
                fromSurface = originalSurfaceId
              } else if (n === 1) {
                direction = "down"
                fromSurface = rowFrontier[0]
              } else if (n === 2) {
                direction = "down"
                fromSurface = originalSurfaceId
              } else {
                const rowIdx = (n - 3) % 3
                direction = "right"
                fromSurface = rowFrontier[rowIdx]
              }

              const surfaceId = await createSplit($, direction, fromSurface)
              if (!surfaceId) return

              if (n < 3) {
                rowFrontier[n] = surfaceId
              } else {
                const rowIdx = (n - 3) % 3
                rowFrontier[rowIdx] = surfaceId
              }

              activeSplits.set(info.id, surfaceId)
              agentCount++

              const attachCmd = `opencode attach ${url} --session ${info.id}`
              await sendToSurface($, surfaceId, attachCmd)
              await sendKeyToSurface($, surfaceId, "enter")

              if (originalSurfaceId) {
                await focusSurface($, originalSurfaceId)
              }
            })
          }
        }
        return
      }

      if (e.type === "session.deleted") {
        const info = e.properties.info
        if (info?.id) removeAndClose(info.id)
        return
      }

      if (e.type === "session.status") {
        const { sessionID, status } = e.properties

        if (status.type === "busy") {
          if (!isWaitingForInput()) {
            await setStatus($, "opencode", "working", {
              icon: "terminal",
              color: "#f59e0b",
            })
          }
          return
        }

        if (status.type === "idle") {
          if (isWaitingForInput()) {
            return
          }

          const session = await fetchSession(sessionID)
          const title = session?.title ?? sessionID

          if (!session?.parentID) {
            if (notifyOn.done) await notify($, { title: `Done: ${title}` })
            await log($, `Done: ${title}`, { level: "success", source: "opencode" })
            await clearStatus($, "opencode")
          } else {
            await log($, `Subagent finished: ${title}`, {
              level: "info",
              source: "opencode",
            })

            removeAndClose(sessionID)
          }
          return
        }
      }

      if (e.type === "session.error") {
        pendingPermissions.clear()
        pendingQuestions.clear()

        const sessionID = e.properties.sessionID
        const title = sessionID
          ? (await fetchSession(sessionID))?.title ?? sessionID
          : "unknown session"

        if (notifyOn.error) await notify($, { title: `Error: ${title}` })
        await log($, `Error in session: ${title}`, {
          level: "error",
          source: "opencode",
        })
        await clearStatus($, "opencode")

        if (sessionID) removeAndClose(sessionID)
        return
      }

      if (e.type === "permission.asked" || e.type === "permission.updated") {
        const id = getPermissionRequestID(e.properties)
        if (id && !pendingPermissions.has(id)) {
          pendingPermissions.add(id)
          const title = e.properties.title ?? e.properties.permission ?? "command"
          await setStatus($, "opencode", "waiting", {
            icon: "lock",
            color: "#ef4444",
          })
          if (notifyOn.permission)
            await notify($, { title: "Needs your permission", subtitle: title })
          await log($, `Permission requested: ${title}`, {
            level: "info",
            source: "opencode",
          })
        }
        return
      }

      if (e.type === "permission.replied") {
        const id = getPermissionRequestID(e.properties)
        if (id) {
          pendingPermissions.delete(id)
        }

        if (!isWaitingForInput()) {
          await setStatus($, "opencode", "working", {
            icon: "terminal",
            color: "#f59e0b",
          })
        }
        return
      }

      if (e.type === "question.asked") {
        const id = getQuestionRequestID(e.properties)
        if (id) {
          pendingQuestions.add(id)
        }

        const header = e.properties.questions?.[0]?.header ?? "Question"
        await setStatus($, "opencode", "question", {
          icon: "help-circle",
          color: "#a855f7",
        })
        if (notifyOn.question)
          await notify($, { title: "Has a question", subtitle: header })
        await log($, `Question: ${header}`, { level: "info", source: "opencode" })
        return
      }

      if (e.type === "question.replied" || e.type === "question.rejected") {
        const id = getQuestionRequestID(e.properties)
        if (id) {
          pendingQuestions.delete(id)
        }

        if (!isWaitingForInput()) {
          await setStatus($, "opencode", "working", {
            icon: "terminal",
            color: "#f59e0b",
          })
        }
        return
      }
    },

    async "permission.ask"(input) {
      const id = getPermissionRequestID(input as any)
      if (id) {
        pendingPermissions.add(id)
      }

      const title = (input as any).title ?? (input as any).permission ?? "command"
      await setStatus($, "opencode", "waiting", {
        icon: "lock",
        color: "#ef4444",
      })
      if (notifyOn.permission)
        await notify($, { title: "Needs your permission", subtitle: title })
      await log($, `Permission requested: ${title}`, {
        level: "info",
        source: "opencode",
      })
    },
  }
}

export default plugin
