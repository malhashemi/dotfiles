// cmux-opencode-session-plugin-marker v1
// Bridges OpenCode session lifecycle events into cmux's restorable session store.
// Installed by `cmux hooks opencode install` or `cmux hooks setup`.
// DO NOT EDIT MANUALLY. cmux upgrades this file in place.

import { spawnSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

const CMUX_PLUGIN_INSTALLED_KEY = Symbol.for("cmux.session.restore.plugin.installed");

function firstString(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim().length > 0) return value.trim();
  }
  return null;
}

function eventProperties(event) {
  return (event && typeof event === "object" && event.properties) || {};
}

function sessionIdFor(event) {
  const props = eventProperties(event);
  return firstString(
    props.info && props.info.id,
    props.sessionID,
    props.sessionId,
    props.session_id,
    props.session && props.session.id,
    event && event.sessionID,
    event && event.sessionId,
    event && event.id
  );
}

function cwdFor(ctx, event) {
  const props = eventProperties(event);
  return firstString(
    props.info && props.info.directory,
    props.cwd,
    props.directory,
    ctx && ctx.directory,
    process.cwd()
  );
}

function resolveExecutable(name) {
  const pathEnv = process.env.PATH || "";
  for (const dir of pathEnv.split(path.delimiter)) {
    if (!dir) continue;
    const candidate = path.join(dir, name);
    try {
      fs.accessSync(candidate, fs.constants.X_OK);
      return candidate;
    } catch (_) {}
  }
  return name;
}

function looksLikeOpenCodeScript(value) {
  if (!value) return false;
  const lower = String(value).toLowerCase();
  return lower.includes("opencode") || lower.includes("open-code");
}

function isOpenCodeInternalWorkerArg(value) {
  if (!value) return false;
  const normalized = String(value).replaceAll("\\", "/");
  return normalized.includes("/$bunfs/") && normalized.includes("/src/cli/cmd/tui/worker.js");
}

function withoutOpenCodeInternalWorkerArgs(argv) {
  const result = [];
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (i > 0 && isOpenCodeInternalWorkerArg(value)) continue;
    result.push(value);
  }
  return result.length > 0 ? result : [resolveExecutable("opencode")];
}

function normalizedLaunchArgv() {
  const raw = Array.isArray(process.argv) ? process.argv.map((value) => String(value)) : [];
  if (raw.length === 0) return [resolveExecutable("opencode")];

  const firstBase = path.basename(raw[0]).toLowerCase();
  if (looksLikeOpenCodeScript(firstBase)) return withoutOpenCodeInternalWorkerArgs(raw);

  let tail = raw.slice(1);
  if (tail.length > 0 && looksLikeOpenCodeScript(tail[0])) {
    tail = tail.slice(1);
  }
  return withoutOpenCodeInternalWorkerArgs([resolveExecutable("opencode"), ...tail]);
}

function base64NulSeparated(values) {
  const bytes = [];
  for (const value of values) {
    bytes.push(Buffer.from(String(value), "utf8"));
    bytes.push(Buffer.from([0]));
  }
  return Buffer.concat(bytes).toString("base64");
}

function hookEnvironment(cwd) {
  const env = { ...process.env };
  delete env.AMP_API_KEY;
  if (!env.CMUX_AGENT_LAUNCH_ARGV_B64) {
    const argv = normalizedLaunchArgv();
    env.CMUX_AGENT_LAUNCH_KIND = "opencode";
    env.CMUX_AGENT_LAUNCH_EXECUTABLE = argv[0] || resolveExecutable("opencode");
    env.CMUX_AGENT_LAUNCH_ARGV_B64 = base64NulSeparated(argv);
    env.CMUX_AGENT_LAUNCH_CWD = cwd || process.cwd();
  }
  return env;
}

function sendHook(subcommand, ctx, event, extra = {}) {
  if (process.env.CMUX_OPENCODE_HOOKS_DISABLED === "1") return;
  if (!process.env.CMUX_SURFACE_ID) return;

  const sessionId = sessionIdFor(event);
  if (!sessionId) return;

  const cwd = cwdFor(ctx, event);
  const payload = {
    session_id: sessionId,
    cwd,
    event: event && event.type,
    hook_event_name: event && event.type,
    ...extra,
  };
  const cmux = process.env.CMUX_OPENCODE_CMUX_BIN || "cmux";
  try {
    spawnSync(cmux, ["hooks", "opencode", subcommand], {
      input: JSON.stringify(payload),
      encoding: "utf8",
      env: hookEnvironment(cwd),
      stdio: ["pipe", "ignore", "ignore"],
      timeout: 5000,
    });
  } catch (_) {}
}

const CMUXSessionRestore = async (ctx) => {
  if (globalThis[CMUX_PLUGIN_INSTALLED_KEY]) return {};
  globalThis[CMUX_PLUGIN_INSTALLED_KEY] = true;
  return {
    event: async ({ event }) => {
      const props = eventProperties(event);
      switch (event && event.type) {
        case "session.created":
          sendHook("session-start", ctx, event);
          break;
        case "session.updated":
          if (props.info && props.info.time && props.info.time.archived) {
            sendHook("session-end", ctx, event);
          } else {
            sendHook("session-start", ctx, event);
          }
          break;
        case "session.status":
          if (props.status && props.status.type === "idle") {
            sendHook("stop", ctx, event);
          }
          break;
        case "session.idle":
          sendHook("stop", ctx, event);
          break;
        case "session.deleted":
          sendHook("session-end", ctx, event);
          break;
        default:
          break;
      }
    },
  };
};

export { CMUXSessionRestore };
export default CMUXSessionRestore;