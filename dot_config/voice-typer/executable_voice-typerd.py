#!/usr/bin/env python3
"""voice-typerd — local voice-dictation orchestrator.

Pipeline: F7 (via voice-ctl) -> activation state machine -> Parakeet (parakeet
serve, warm) -> context capture (window/screenshot/selection) -> pi smart/intent
layer -> output (wtype + clipboard) + quickshell HUD.

Pure stdlib (works on the system Python 3.14; no ML deps live here — Parakeet is
an external Rust binary). See config.toml for tunables.
"""

from __future__ import annotations

import base64
import json
import os
import queue
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path.home()
CONFIG_PATH = HOME / ".config/voice-typer/config.toml"
SYSPROMPT_PATH = HOME / ".config/voice-typer/smart-transcriber.system.md"
COMMAND_SYSPROMPT_PATH = HOME / ".config/voice-typer/smart-command.system.md"
TRANSLATE_SYSPROMPT_PATH = HOME / ".config/voice-typer/smart-translate.system.md"
HUD_INSTANCE = HOME / ".config/quickshell/voice"


def _run_dir() -> Path:
    base = os.environ.get("XDG_RUNTIME_DIR")
    d = Path(base) / "voice-typer" if base else HOME / ".config/voice-typer/run"
    d.mkdir(parents=True, exist_ok=True)
    try:
        d.chmod(0o700)
    except OSError:
        pass
    return d


RUNDIR = _run_dir()
CONTROL_SOCK = RUNDIR / "control.sock"
PARAKEET_SOCK = RUNDIR / "parakeet.sock"
PARAKEET_PID = RUNDIR / "parakeet.pid"
SHOT_PATH = RUNDIR / "shot.png"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME") or (HOME / ".cache")) / "voice-typer"
LAST_WAV = CACHE_DIR / "last-recording.wav"
LAST_PAYLOAD = CACHE_DIR / "last-payload.txt"
LAST_RESPONSE = CACHE_DIR / "last-response.txt"


def log(*a: object) -> None:
    print("[voice-typerd]", *a, file=sys.stderr, flush=True)


def notify(summary: str, body: str = "", urgency: str = "normal") -> None:
    """Best-effort desktop notification so cloud failures are never silent.
    Linux: notify-send (libnotify/swaync). macOS: osascript. No-ops if the tool
    is missing."""
    if sys.platform == "darwin":
        if shutil.which("osascript") is None:
            return
        def _esc(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')
        script = f'display notification "{_esc(body)}" with title "{_esc(summary)}"'
        try:
            subprocess.run(["osascript", "-e", script], timeout=3,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            pass
        return
    if shutil.which("notify-send") is None:
        return
    try:
        subprocess.run(
            ["notify-send", "-a", "voice-typer", "-u", urgency, summary, body],
            timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


# ── Config ──────────────────────────────────────────────────────────────────

DEFAULTS: dict = {
    "model": {"name": "openai/gpt-5.5", "thinking": "off"},
    "stt": {
        "device": "",
        "model_dir": "",
        "silence_ms": 1500,
        "vad_threshold": 0.5,
        "idle_shutdown_secs": 900,
        "prewarm": False,
    },
    "activation": {"tap_ms": 250, "double_tap_ms": 350, "commit_timeout_secs": 12},
    "context": {
        "screen_context": "ocr",
        "ocr_lang": "eng",
        "ocr_max_chars": 6000,
        "screenshot_active_window": True,
        "screenshot_max_width": 1200,
        "send_selection": True,
    },
    "output": {"keep_on_clipboard": True, "method": "paste", "paste_delay_ms": 100},
    "audio": {
        "duck_while_recording": True,
        "duck_volume": 0.1,
        "boost_mic_while_recording": True,
        "mic_boost_volume": 1.0,
    },
    "multilingual": {
        "preprocess": True,
        "trim_silence": True,
        "silence_threshold_db": -40,
        "silence_min_secs": 1.0,
    },
    "debug": {"save_recordings": False},
    "hud": {"enabled": True},
    "commands": {
        "screenshot": ["grim", "{path}"],
        "window_info": ["hyprctl", "activewindow", "-j"],
        "type_text": ["wtype", "-s", "120", "-d", "8", "--", "{text}"],
        "copy": ["wl-copy"],
        "paste_primary": ["wl-paste", "--primary", "--no-newline"],
        "paste": ["~/.config/hypr/scripts/smart-clipboard.sh", "paste"],
        "record_audio": ["pw-record", "{path}"],
    },
}


def load_config() -> dict:
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    try:
        with open(CONFIG_PATH, "rb") as f:
            user = tomllib.load(f)
        for section, vals in user.items():
            cfg.setdefault(section, {})
            if isinstance(vals, dict):
                cfg[section].update(vals)
            else:
                cfg[section] = vals
    except FileNotFoundError:
        log(f"config not found at {CONFIG_PATH}; using defaults")
    except (tomllib.TOMLDecodeError, OSError) as e:
        log(f"config error ({e}); using defaults")
    return cfg


# ── HUD (best-effort quickshell IPC) ─────────────────────────────────────────

class Hud:
    def __init__(self, enabled: bool):
        self.enabled = enabled and shutil.which("qs") is not None

    def call(self, fn: str, *args: str) -> None:
        if not self.enabled:
            return
        argv = ["qs", "-p", str(HUD_INSTANCE), "ipc", "call", "voice", fn, *map(str, args)]
        try:
            subprocess.run(argv, timeout=2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            pass


# ── Parakeet engine (parakeet serve) ─────────────────────────────────────────

_UTT_RE = re.compile(r"\[daemon\] Transcribed(?: \(final\))?: (.*)")


class Engine:
    """Manages one warm `parakeet serve` subprocess and its control socket."""

    def __init__(self, cfg: dict, events: "queue.Queue"):
        self.cfg = cfg
        self.events = events
        self.proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def _build_argv(self) -> list[str]:
        argv = ["parakeet", "serve", "--socket", str(PARAKEET_SOCK), "--pid-file", str(PARAKEET_PID)]
        dev = self.cfg["stt"].get("device") or ""
        if dev:
            argv += ["--device", dev]
        mdir = self.cfg["stt"].get("model_dir") or ""
        if mdir:
            argv += ["--model-dir", mdir]
        return argv

    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def ensure_ready(self, timeout: float = 30.0) -> bool:
        """Start serve if needed and wait until its socket accepts connections."""
        with self._lock:
            if not self.alive():
                self._spawn()
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if not self.alive():
                    log("parakeet serve exited during startup")
                    return False
                try:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.settimeout(1.0)
                        s.connect(str(PARAKEET_SOCK))
                    return True
                except OSError:
                    time.sleep(0.1)
            log("timed out waiting for parakeet serve socket")
            return False

    def _spawn(self) -> None:
        for stale in (PARAKEET_SOCK, PARAKEET_PID):
            try:
                stale.unlink()
            except OSError:
                pass
        argv = self._build_argv()
        log("starting:", " ".join(argv))
        try:
            self.proc = subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1,
            )
        except FileNotFoundError:
            log("ERROR: `parakeet` not found on PATH. Install parakeet-cli.")
            self.proc = None
            return
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        p = self.proc
        if p is None or p.stdout is None:
            return
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.strip():
                self.events.put(("session", line.strip()))
        self.events.put(("engine_exit",))

    def _read_stderr(self) -> None:
        p = self.proc
        if p is None or p.stderr is None:
            return
        for line in p.stderr:
            line = line.rstrip("\n")
            m = _UTT_RE.search(line)
            if m:
                self.events.put(("utt", m.group(1).strip()))
            elif "No speech detected in session" in line:
                self.events.put(("nospeech",))
            elif line.strip():
                log("serve:", line.strip())

    def cmd(self, command: str) -> dict | None:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(3.0)
                s.connect(str(PARAKEET_SOCK))
                s.sendall(command.encode())
                data = s.recv(4096)
            return json.loads(data.decode() or "{}")
        except (OSError, json.JSONDecodeError) as e:
            log(f"parakeet cmd {command!r} failed: {e}")
            return None

    def start_recording(self) -> bool:
        if not self.ensure_ready():
            return False
        return self.cmd("start") is not None

    def stop_recording(self) -> None:
        self.cmd("stop")

    def cancel(self) -> None:
        self.cmd("cancel")

    def shutdown(self) -> None:
        with self._lock:
            if self.alive():
                self.cmd("shutdown")
                try:
                    self.proc.wait(timeout=5)  # type: ignore[union-attr]
                except (subprocess.TimeoutExpired, AttributeError):
                    if self.proc:
                        self.proc.terminate()
            self.proc = None


# ── Context capture ──────────────────────────────────────────────────────────

def _run(argv: list[str], timeout: float = 5.0, stdin: str | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            argv, input=stdin, capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode, r.stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"cmd failed {argv[:2]}: {e}")
        return 1, ""


def _subst(argv: list[str], **kw: str) -> list[str]:
    out = []
    for a in argv:
        for k, v in kw.items():
            a = a.replace("{" + k + "}", v)
        out.append(a)
    return out


def _capture_window_png(cfg: dict, geom: str | None) -> str | None:
    """Grab the active window (preferred) or full screen to a PNG."""
    sc = cfg["commands"].get("screenshot") or []
    if not sc:
        return None
    raw = RUNDIR / "shot_raw.png"
    try:
        raw.unlink()
    except OSError:
        pass
    if cfg["context"].get("screenshot_active_window", True) and geom and sc and sc[0] == "grim":
        argv = ["grim", "-g", geom, str(raw)]
    else:
        argv = _subst(sc, path=str(raw))
    code, _ = _run(argv, timeout=8.0)
    if code == 0 and raw.exists() and raw.stat().st_size > 0:
        return str(raw)
    return None


def _ocr(cfg: dict, png: str) -> str:
    """Cheap local OCR of the captured window (no vision model needed)."""
    if shutil.which("tesseract") is None:
        log("tesseract not installed; skipping screen OCR (text-only context)")
        return ""
    lang = cfg["context"].get("ocr_lang", "eng")
    code, out = _run(["tesseract", png, "stdout", "--psm", "6", "-l", lang], timeout=10.0)
    if code != 0:
        return ""
    text = "\n".join(ln for ln in out.splitlines() if ln.strip())
    limit = int(cfg["context"].get("ocr_max_chars", 2000) or 2000)
    return text[:limit]


def _downscale(cfg: dict, png: str) -> str:
    maxw = int(cfg["context"].get("screenshot_max_width", 1200) or 0)
    if maxw <= 0 or shutil.which("magick") is None:
        return png
    jpg = str(RUNDIR / "shot.jpg")
    code, _ = _run(["magick", png, "-resize", f"{maxw}x{maxw}>", "-quality", "80", jpg], timeout=8.0)
    if code == 0 and Path(jpg).exists() and Path(jpg).stat().st_size > 0:
        return jpg
    return png


def capture_context(cfg: dict) -> dict:
    cmds = cfg["commands"]
    ctx: dict = {"app": "", "title": "", "selection": "", "screen_text": "", "shot": None}

    geom = None
    wi = cmds.get("window_info") or []
    if wi:
        code, out = _run(wi)
        if code == 0 and out.strip():
            try:
                j = json.loads(out)
                ctx["app"] = j.get("class") or j.get("app") or ""
                ctx["title"] = j.get("title") or ""
                at, size = j.get("at"), j.get("size")
                if (isinstance(at, list) and isinstance(size, list)
                        and len(at) == 2 and len(size) == 2 and size[0] > 0 and size[1] > 0):
                    geom = f"{at[0]},{at[1]} {size[0]}x{size[1]}"
            except json.JSONDecodeError:
                ctx["app"] = out.strip().splitlines()[0][:120]

    if cfg["context"].get("send_selection"):
        ps = cmds.get("paste_primary") or []
        if ps:
            code, out = _run(ps)
            if code == 0:
                ctx["selection"] = out.strip()

    mode = cfg["context"].get("screen_context", "ocr")
    if mode in ("ocr", "screenshot"):
        png = _capture_window_png(cfg, geom)
        if png and mode == "ocr":
            ctx["screen_text"] = _ocr(cfg, png)
        elif png and mode == "screenshot":
            ctx["shot"] = _downscale(cfg, png)
    return ctx


# ── pi smart/intent layer ────────────────────────────────────────────────────

DICT_FALLBACK = "Clean the user's dictated words and return ONLY the cleaned text, plain, nothing else."
CMD_FALLBACK = "Carry out the user's spoken instruction using the context; return ONLY the resulting text to type."
TRANSLATE_FALLBACK = "Transcribe the attached audio (may mix Arabic and English) and return ONLY the English text, plain."


def _load_prompt(path: Path, fallback: str) -> str:
    try:
        return path.read_text()
    except OSError:
        return fallback


def build_payload(text: str, ctx: dict) -> str:
    parts = []
    app = ctx.get("app", "")
    title = ctx.get("title", "")
    if app:
        parts.append(f"APP: {app}" + (f" — {title}" if title else ""))
    if ctx.get("selection"):
        parts.append("SELECTED_TEXT:\n" + ctx["selection"])
    if ctx.get("screen_text"):
        parts.append("SCREEN_TEXT:\n" + ctx["screen_text"])
    parts.append("RAW_ASR:\n" + text)
    return "\n\n".join(parts)


def _clean_output(s: str) -> str:
    """Extract the plain text the model should return; tolerate stray fences,
    surrounding quotes, or a legacy {"text": ...} JSON object."""
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s).strip()
    if s.startswith("{") and '"text"' in s:
        try:
            d = json.loads(s)
            if isinstance(d, dict) and isinstance(d.get("text"), str):
                s = d["text"].strip()
        except json.JSONDecodeError:
            pass
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1].strip()
    return s


def refine(cfg: dict, payload: str, shot: str | None, system_prompt: str) -> tuple[str, str]:
    """Run the pi smart layer. Returns (text, error): error is "" on success — even
    if the model legitimately produced empty text — and a short reason string when
    the call itself failed (pi missing, non-zero exit: no API credit, network, …).
    pi's stderr (the real reason) is logged."""
    if shutil.which("pi") is None:
        log("WARNING: `pi` not found")
        return "", "pi not installed"
    argv = [
        "pi", "-p", "--no-tools", "--no-session",
        "--thinking", cfg["model"].get("thinking", "off"),
        "--model", cfg["model"].get("name", "google/gemini-2.5-flash"),
        "--system-prompt", system_prompt,
    ]
    if shot:
        argv.append("@" + shot)
    argv.append(payload)
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=30.0)
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"pi call failed: {e}")
        return "", f"pi {type(e).__name__}"
    if r.returncode != 0:
        reason = " ".join((r.stderr or "").split())[:200]
        log(f"pi exited {r.returncode}: {reason}")
        return "", f"exit {r.returncode}"
    return _clean_output(r.stdout), ""


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def gemini_audio(cfg: dict, payload: str, wav_path: Path, system_prompt: str,
                 shot: str | None = None) -> tuple[str, str]:
    """Transcribe/translate spoken audio by calling the Gemini API directly with
    the audio inlined, plus the same context as the other modes (APP/SELECTED_TEXT/
    SCREEN_TEXT ride in `payload`; a screenshot, when enabled, is inlined here).

    `pi`'s @file attachments only carry text and images — audio is silently
    dropped — so the multilingual path must talk to Gemini itself or the model
    just parrots the text context. Returns (text, error): error is "" on success,
    else a short reason (no key, HTTP code, network) so failures are never silent.
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        log("WARNING: GEMINI_API_KEY not set — cannot transcribe audio")
        return "", "no GEMINI_API_KEY"
    model = cfg["model"].get("name", "google/gemini-2.5-flash").split("/")[-1]
    try:
        audio_b64 = base64.b64encode(wav_path.read_bytes()).decode()
    except OSError as e:
        log(f"gemini audio: cannot read {wav_path}: {e}")
        return "", "cannot read audio"
    req_parts: list[dict] = [
        {"text": payload},
        {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}},
    ]
    # Screenshot context (screen_context = "screenshot"): inline it too, the way
    # the other modes hand it to pi via @shot.
    if shot:
        try:
            sp = Path(shot)
            mime = "image/jpeg" if sp.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            req_parts.append({"inline_data": {
                "mime_type": mime,
                "data": base64.b64encode(sp.read_bytes()).decode(),
            }})
        except OSError as e:
            log(f"gemini audio: cannot read screenshot {shot}: {e}")
    body = json.dumps({
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": req_parts}],
        "generationConfig": {"temperature": 0.0},
    }).encode()
    req = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=model), data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        log(f"gemini audio HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
        return "", f"HTTP {e.code}"
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        log(f"gemini audio request failed: {e}")
        return "", "network error"
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError):
        log(f"gemini audio: no candidate in response ({json.dumps(data)[:200]})")
        return "", "no response (blocked?)"
    return _clean_output(text), ""


def _preprocess_audio(cfg: dict, src: Path) -> Path:
    """Normalize the recording before cloud upload: downsample to 16 kHz mono
    (Gemini downsamples to that anyway — ~6x smaller upload) and optionally strip
    long silences (fewer audio tokens; avoids the inline-size limit on long takes).
    Needs ffmpeg; on any failure returns the original file so multilingual still works.
    """
    mc = cfg.get("multilingual", {})
    if not mc.get("preprocess", True):
        return src
    if shutil.which("ffmpeg") is None:
        log("ffmpeg not found; sending original audio")
        return src
    out = RUNDIR / "upload.wav"
    argv = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src)]
    if mc.get("trim_silence", True):
        thr = mc.get("silence_threshold_db", -40)
        gap = mc.get("silence_min_secs", 1.0)
        argv += ["-af",
                 f"silenceremove=start_periods=1:start_duration=0:start_threshold={thr}dB:"
                 f"stop_periods=-1:stop_duration={gap}:stop_threshold={thr}dB"]
    argv += ["-ar", "16000", "-ac", "1", str(out)]
    code, _ = _run(argv, timeout=30.0)
    if code == 0 and out.exists() and out.stat().st_size > 1024:
        try:
            log(f"audio preprocess: {src.stat().st_size // 1024}KB -> {out.stat().st_size // 1024}KB")
        except OSError:
            pass
        return out
    log("audio preprocess failed; sending original")
    return src


# ── Output ───────────────────────────────────────────────────────────────────

def copy_text(cfg: dict, text: str) -> None:
    cp = cfg["commands"].get("copy") or []
    if not cp:
        return
    # wl-copy double-forks a daemon to own the selection; capturing its pipes
    # would block until the clipboard is overwritten. Detach + DEVNULL instead.
    try:
        subprocess.run(
            cp, input=text, text=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5, start_new_session=True,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"copy failed: {e}")


def type_text(cfg: dict, text: str) -> None:
    tt = cfg["commands"].get("type_text") or []
    if tt:
        _run(_subst(tt, text=text), timeout=30.0)


def paste(cfg: dict) -> None:
    """Trigger the platform paste shortcut so the focused app inserts the clipboard
    (Linux: smart-clipboard.sh -> ALT+V in terminals / CTRL+V in GUI; macOS: Cmd+V).
    Pasting inserts the text wholesale, sidestepping wtype's per-key capital issues."""
    p = cfg["commands"].get("paste") or []
    if not p:
        return
    argv = [os.path.expanduser(a) for a in p]
    if shutil.which(argv[0]) is None and not os.path.exists(argv[0]):
        log(f"paste command not found: {argv[0]}")
        return
    _run(argv, timeout=5.0)


def commit_output(cfg: dict, text: str, hud: Hud) -> None:
    text = (text or "").strip()
    if not text:
        return
    # Durable copy of every committed dictation, independent of the clipboard and
    # the clipboard-history managers (which can race and silently drop a transient
    # value). Lets `voice-ctl paste-last` re-insert the last result on demand even
    # if the live clipboard has since moved on.
    try:
        LAST_RESPONSE.parent.mkdir(parents=True, exist_ok=True)
        LAST_RESPONSE.write_text(text)
    except OSError as e:
        log(f"could not persist last response: {e}")
    hud.call("setRefined", text)
    out = cfg["output"]
    if out.get("method", "paste") == "paste" and cfg["commands"].get("paste"):
        # Copy, then paste: the app inserts the clipboard in one shot (no per-key
        # synthesis), which is reliable for capitals/unicode. The small delay lets
        # the clipboard manager claim the selection before the paste fires.
        copy_text(cfg, text)
        time.sleep(float(out.get("paste_delay_ms", 100)) / 1000.0)
        paste(cfg)
    else:
        if out.get("keep_on_clipboard", True):
            copy_text(cfg, text)
        type_text(cfg, text)


# ── Control socket server ────────────────────────────────────────────────────

def serve_control(events: "queue.Queue") -> None:
    for stale in (CONTROL_SOCK,):
        try:
            stale.unlink()
        except OSError:
            pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(str(CONTROL_SOCK))
    try:
        CONTROL_SOCK.chmod(0o600)
    except OSError:
        pass
    srv.listen(8)
    log(f"control socket: {CONTROL_SOCK}")
    while True:
        try:
            conn, _ = srv.accept()
        except OSError:
            break
        with conn:
            try:
                data = conn.recv(64).decode().strip()
            except OSError:
                continue
            if data:
                parts = data.splitlines()[0].strip().lower().split()
                if parts:
                    cmd = parts[0]
                    mode = parts[1] if len(parts) > 1 else "dictate"
                    events.put(("ctl", cmd, mode))
            try:
                conn.sendall(b"ok")
            except OSError:
                pass


# ── State machine / app ──────────────────────────────────────────────────────

IDLE, HOLD, PENDING_LOCK, LOCKED, COMMITTING = "idle", "hold", "pending_lock", "locked", "committing"


class App:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.events: queue.Queue = queue.Queue()
        self.engine = Engine(cfg, self.events)
        self.hud = Hud(cfg["hud"].get("enabled", True))
        self.state = IDLE
        self.session_mode = "dictate"   # "dictate" | "command"
        self.t_down = 0.0
        self.ignore_next_up = False
        self.live: list[str] = []
        self._dbl_timer: threading.Timer | None = None
        self._commit_timer: threading.Timer | None = None
        self._idle_timer: threading.Timer | None = None
        self._hide_timer: threading.Timer | None = None
        self._ducked_vol: float | None = None
        self._mic_vol: float | None = None
        self._rec_proc: subprocess.Popen | None = None

    # --- timers (push events into the queue) ---
    def _arm(self, attr: str, secs: float, ev: tuple) -> None:
        self._cancel(attr)
        t = threading.Timer(secs, lambda: self.events.put(ev))
        t.daemon = True
        setattr(self, attr, t)
        t.start()

    def _cancel(self, attr: str) -> None:
        t = getattr(self, attr, None)
        if t is not None:
            t.cancel()
            setattr(self, attr, None)

    # --- recording lifecycle ---
    def _start_recording(self, locked: bool) -> None:
        self._cancel("_idle_timer")
        self._cancel("_hide_timer")
        self.live = []
        self.hud.call("reveal")
        if self.session_mode == "multilingual":
            # Mode 4 is Parakeet-independent by design: the language (e.g. Iraqi
            # Arabic) is one Parakeet can't read, so the audio goes straight to
            # Gemini. Capture with pw-record only and never start Parakeet — its
            # Silero VAD must not be able to veto the upload (it once flagged a
            # healthy 67s take as "no speech" and silently dropped it). No model
            # load here, so skip the "loading" HUD state and go straight to live.
            self._boost_mic()
            self._start_audio_dump()
            if self._rec_proc is None:
                self._restore_mic()
                self.hud.call("setState", "error")
                self._finish_idle(0.8)
                return
            self.hud.call("setState", "locked" if locked else "listening")
            self.state = LOCKED if locked else HOLD
            self._duck()
            return
        # Show "loading" during the (possibly ~2-3s) cold model load, then flip
        # to listening once the engine is actually capturing.
        self.hud.call("setState", "loading")
        self._boost_mic()
        if not self.engine.start_recording():
            self._restore_mic()
            self.hud.call("setState", "error")
            self._finish_idle(0.8)
            return
        self.hud.call("setState", "locked" if locked else "listening")
        self.state = LOCKED if locked else HOLD
        self._duck()
        self._start_audio_dump()

    def _stop_and_commit(self) -> None:
        self.hud.call("setState", "processing")
        if self.session_mode == "multilingual":
            # No Parakeet to stop and no transcript to wait for: finalize the WAV
            # (pw-record) and hand it straight to the Gemini pipeline. This skips
            # the `session`/`nospeech`/commit-timeout event gate entirely — the
            # _preprocess_audio() trim+downsample still runs inside the pipeline.
            self._stop_audio_dump()
            self._restore_mic()
            self._unduck()
            self.state = COMMITTING
            threading.Thread(target=self._pipeline, args=("",), daemon=True).start()
            return
        self.engine.stop_recording()
        self._stop_audio_dump()
        self._restore_mic()
        self._unduck()
        self.state = COMMITTING
        secs = float(self.cfg["activation"].get("commit_timeout_secs", 12))
        self._arm("_commit_timer", secs, ("commit_timeout",))

    def _schedule_idle(self) -> None:
        secs = float(self.cfg["stt"].get("idle_shutdown_secs", 0) or 0)
        if secs > 0:
            self._arm("_idle_timer", secs, ("idle_timeout",))

    def _duck(self) -> None:
        """Lower the default sink to a fraction of its volume while talking."""
        audio = self.cfg.get("audio", {})
        if not audio.get("duck_while_recording", True) or shutil.which("wpctl") is None:
            return
        factor = float(audio.get("duck_volume", 0.1))
        code, out = _run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
        m = re.search(r"Volume:\s*([0-9.]+)", out) if code == 0 else None
        if not m:
            return
        cur = float(m.group(1))
        if cur <= 0:
            return
        _run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{cur * factor:.4f}"])
        self._ducked_vol = cur
        log(f"ducked default sink {cur:.2f} -> {cur * factor:.2f}")

    def _unduck(self) -> None:
        cur = self._ducked_vol
        self._ducked_vol = None
        if cur is not None:
            _run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{cur:.4f}"])
            log(f"restored default sink -> {cur:.2f}")

    def _boost_mic(self) -> None:
        """Raise the default source (mic) while recording for cleaner capture."""
        audio = self.cfg.get("audio", {})
        if not audio.get("boost_mic_while_recording", True) or shutil.which("wpctl") is None:
            return
        target = float(audio.get("mic_boost_volume", 1.0))
        code, out = _run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])
        m = re.search(r"Volume:\s*([0-9.]+)", out) if code == 0 else None
        if not m:
            return
        self._mic_vol = float(m.group(1))
        _run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", f"{target:.4f}"])
        log(f"boosted mic {self._mic_vol:.2f} -> {target:.2f}")

    def _restore_mic(self) -> None:
        cur = self._mic_vol
        self._mic_vol = None
        if cur is not None:
            _run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", f"{cur:.4f}"])
            log(f"restored mic -> {cur:.2f}")

    def _start_audio_dump(self) -> None:
        """Save the mic capture to a WAV (for debug listening, and required by
        multilingual mode, which sends the audio itself to the model). Uses the
        platform `record_audio` command from config (pw-record on Linux, ffmpeg
        avfoundation on macOS)."""
        if not (self.cfg.get("debug", {}).get("save_recordings", False)
                or self.session_mode == "multilingual"):
            return
        rec = self.cfg["commands"].get("record_audio") or []
        if not rec or shutil.which(rec[0]) is None:
            if self.session_mode == "multilingual":
                log(f"multilingual needs audio but record_audio is unavailable: {rec[:1]}")
            return
        try:
            LAST_WAV.parent.mkdir(parents=True, exist_ok=True)
            self._rec_proc = subprocess.Popen(
                _subst(rec, path=str(LAST_WAV)),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            log(f"saving recording -> {LAST_WAV}")
        except OSError as e:
            log(f"audio dump failed: {e}")
            self._rec_proc = None

    def _stop_audio_dump(self) -> None:
        p = self._rec_proc
        self._rec_proc = None
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()

    def _finish_idle(self, delay: float = 1.5) -> None:
        # Keep the HUD up briefly so the result/state is visible, then hide.
        self._cancel("_commit_timer")
        self.state = IDLE
        self._stop_audio_dump()
        self._restore_mic()
        self._unduck()
        self._arm("_hide_timer", delay, ("hide_hud",))
        self._schedule_idle()

    def _pipeline(self, text: str) -> None:
        """Runs in a worker thread: context -> pi -> output.

        Reliability rule: the user always gets their words. If the model declines
        (ignore/ask_clarification), returns nothing, or errors, we insert the raw
        transcript rather than nothing.
        """
        mode = self.session_mode
        outcome = "ok"
        try:
            if mode == "local":
                # Pure local: type Parakeet's transcript verbatim. No cloud round
                # trip, no OCR/selection context — instant and offline.
                log(f"local -> {text[:80]!r}")
                commit_output(self.cfg, text, self.hud)
                return
            if mode == "multilingual":
                outcome = self._run_multilingual()
                return
            ctx = capture_context(self.cfg)
            payload = build_payload(text, ctx)
            if mode == "command":
                cleaned, err = refine(self.cfg, payload, ctx.get("shot"),
                                      _load_prompt(COMMAND_SYSPROMPT_PATH, CMD_FALLBACK))
                if err:
                    # No safe local fallback for a command — make the failure loud.
                    log(f"command failed: {err}")
                    notify("Voice command failed", f"AI unavailable ({err}) — nothing typed", "critical")
                    outcome = "error"
                    return
                if not cleaned.strip():
                    log("command produced no output")
                    outcome = "error"
                    return
                log(f"command -> {cleaned[:80]!r}")
            else:
                cleaned, err = refine(self.cfg, payload, ctx.get("shot"),
                                      _load_prompt(SYSPROMPT_PATH, DICT_FALLBACK))
                if err:
                    # Reliability: never lose the user's words — type the raw
                    # transcript, but tell them the AI cleanup was skipped.
                    log(f"dictation AI failed: {err} -> inserting raw transcript")
                    notify("Voice dictation", f"AI cleanup unavailable ({err}) — typed raw transcript")
                    cleaned = text
                elif not cleaned.strip():
                    log("model gave nothing usable -> inserting raw transcript")
                    cleaned = text
                log(f"output -> {cleaned[:80]!r}")
            commit_output(self.cfg, cleaned, self.hud)
        except Exception as e:  # noqa: BLE001 - never let the worker kill the daemon
            log(f"pipeline error: {e}")
            outcome = "error"
            if mode in ("dictate", "local"):  # raw fallback only where it makes sense
                try:
                    commit_output(self.cfg, text, self.hud)
                    outcome = "ok"
                except Exception as e2:  # noqa: BLE001
                    log(f"raw fallback also failed: {e2}")
        finally:
            self.events.put(("commit_done", outcome))

    def _run_multilingual(self) -> str:
        """Transcribe the recorded audio (Iraqi Arabic + English) -> English via
        Gemini directly (pi can't attach audio). The OCR/selection context rides
        along only as a spelling reference for on-screen names. Returns "ok"/"error"
        so the HUD can flag failures; there is no local fallback for Arabic, so a
        cloud failure is surfaced (notification) rather than swallowed."""
        if not LAST_WAV.exists() or LAST_WAV.stat().st_size < 1024:
            log("multilingual: no audio captured")
            return "error"
        ctx = capture_context(self.cfg)
        payload = build_payload("(spoken audio is attached — transcribe and translate to English)", ctx)
        upload = _preprocess_audio(self.cfg, LAST_WAV)
        cleaned, err = gemini_audio(self.cfg, payload, upload,
                                    _load_prompt(TRANSLATE_SYSPROMPT_PATH, TRANSLATE_FALLBACK),
                                    shot=ctx.get("shot"))
        if err:
            log(f"multilingual failed: {err}")
            notify("Multilingual failed", f"AI unavailable ({err}) — nothing typed", "critical")
            return "error"
        if not cleaned.strip():
            log("multilingual: model returned nothing")
            return "ok"  # legit empty (e.g. silence) — not a failure
        log(f"multilingual -> {cleaned[:80]!r}")
        commit_output(self.cfg, cleaned, self.hud)
        return "ok"

    def _paste_last(self) -> None:
        """Type the last committed dictation straight from the durable
        last-response.txt via wtype — never touching the clipboard, so whatever
        you currently have copied is preserved. Triggered by CTRL+ALT+V
        (voice-ctl paste-last). The short delay lets the chord's CTRL+ALT lift
        before wtype injects; otherwise the held modifiers would corrupt the
        characters (and CTRL+<key> in a terminal could fire control codes)."""
        try:
            text = LAST_RESPONSE.read_text().strip()
        except OSError:
            text = ""
        if not text:
            log("paste-last: no saved dictation yet")
            notify("Voice paste", "No saved dictation yet")
            return
        time.sleep(0.2)
        log(f"paste-last -> {text[:80]!r}")
        type_text(self.cfg, text)

    # --- event handling ---
    def on_ctl(self, cmd: str, mode: str = "dictate") -> None:
        if cmd == "paste-last":
            # Re-insert the last dictation from disk; independent of the recording
            # state machine, so run it off-thread and return.
            threading.Thread(target=self._paste_last, daemon=True).start()
            return
        if cmd not in ("down", "up", "toggle"):
            log(f"unknown control command: {cmd}")
            return
        tap_ms = float(self.cfg["activation"].get("tap_ms", 250))
        dbl_ms = float(self.cfg["activation"].get("double_tap_ms", 350))

        if cmd == "toggle":
            if self.state == IDLE:
                self.session_mode = mode
                self._start_recording(locked=True)
            elif self.state in (HOLD, PENDING_LOCK, LOCKED):
                self._cancel("_dbl_timer")
                self._stop_and_commit()
            return

        if cmd == "down":
            if self.state == IDLE:
                self.session_mode = mode
                self.t_down = time.monotonic()
                self._start_recording(locked=False)
            elif self.state == PENDING_LOCK:
                self._cancel("_dbl_timer")
                self.state = LOCKED
                self.hud.call("setState", "locked")
            elif self.state == LOCKED:
                self.ignore_next_up = True
                self._stop_and_commit()
            return

        if cmd == "up":
            if self.state == HOLD:
                held = (time.monotonic() - self.t_down) * 1000.0
                if held < tap_ms:
                    self.state = PENDING_LOCK
                    self._arm("_dbl_timer", dbl_ms / 1000.0, ("dbl_timeout",))
                else:
                    self._stop_and_commit()
            elif self.state == LOCKED:
                self.ignore_next_up = False  # release of the stopping press
            return

    def run(self) -> None:
        threading.Thread(target=lambda: serve_control(self.events), daemon=True).start()
        if self.cfg["stt"].get("prewarm"):
            threading.Thread(target=self.engine.ensure_ready, daemon=True).start()
        log("ready")
        while True:
            ev = self.events.get()
            kind = ev[0]
            if kind == "ctl":
                self.on_ctl(ev[1], ev[2] if len(ev) > 2 else "dictate")
            elif kind == "utt":
                # In multilingual mode the engine's transcript is garbage (it
                # can't do Arabic) — gemini handles the audio; don't show it.
                if self.session_mode != "multilingual":
                    self.live.append(ev[1])
                    log(f"utterance: {ev[1]}")
                    self.hud.call("setRaw", " ".join(self.live))
            elif kind == "session":
                # Mode 4 drives its own pipeline on stop (Parakeet-independent);
                # ignore any transcript a warm engine emits so we never double-fire.
                if self.session_mode != "multilingual" and self.state == COMMITTING:
                    log(f"transcript: {ev[1]}")
                    self._cancel("_commit_timer")
                    threading.Thread(target=self._pipeline, args=(ev[1],), daemon=True).start()
            elif kind == "nospeech":
                # Mode 4 must never be aborted by Parakeet's Silero VAD — that was
                # the bug. Only the local/dictate/command modes honor "no speech".
                if self.session_mode != "multilingual" and self.state == COMMITTING:
                    log("no speech detected")
                    self.hud.call("setRaw", "")
                    self.hud.call("setState", "idle")
                    self._finish_idle(0.6)
            elif kind == "commit_timeout":
                if self.state == COMMITTING:
                    log("commit timed out (no transcript)")
                    self.hud.call("setState", "error")
                    self._finish_idle(0.8)
            elif kind == "commit_done":
                outcome = ev[1] if len(ev) > 1 else "ok"
                if outcome == "error":
                    self.hud.call("setState", "error")
                    self._finish_idle(1.2)
                else:
                    self.hud.call("setState", "idle")
                    self._finish_idle(1.6)
            elif kind == "hide_hud":
                self.hud.call("hide")
            elif kind == "idle_timeout":
                if self.state == IDLE and self.engine.alive():
                    log("idle: shutting down warm model")
                    self.engine.shutdown()
            elif kind == "engine_exit":
                # A warm Parakeet dying mid-take only matters when Parakeet is the
                # input path; mode 4 records via pw-record, so don't let it abort.
                if self.session_mode != "multilingual" and self.state in (HOLD, PENDING_LOCK, LOCKED, COMMITTING):
                    self.hud.call("setState", "error")
                    self._finish_idle()


def main() -> int:
    # single-instance guard via the control socket
    if CONTROL_SOCK.exists():
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                s.connect(str(CONTROL_SOCK))
            log("another voice-typerd is already running; exiting")
            return 0
        except OSError:
            pass  # stale socket; serve_control will unlink it
    cfg = load_config()
    app = App(cfg)

    import signal

    def _term(_sig, _frm):
        log("terminating")
        app.engine.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _term)
    signal.signal(signal.SIGINT, _term)
    try:
        app.run()
    except KeyboardInterrupt:
        app.engine.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
