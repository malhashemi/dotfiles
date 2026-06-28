# voice-typer

Local, push-to-talk voice dictation for Linux/Hyprland (a self-hosted Vibe Typer
replacement). Speech is transcribed **on-device** with NVIDIA Parakeet, optionally
cleaned/acted-on by a cloud model via `pi`, then typed into the focused app with a
quickshell HUD.

```
hotkey → voice-ctl → voice-typerd (state machine)
        → Parakeet (local STT)  → [optional] pi/Gemini smart layer
        → wtype types it + clipboard, with a quickshell HUD
```

Managed by chezmoi. The daemon (`voice-typerd.py`) is pure Python stdlib; all
heavy lifting is external tools (Parakeet binary, pi, ffmpeg, wtype…).

## Modes & keys

| Key | Mode | STT | Smart layer | Context sent |
|-----|------|-----|-------------|--------------|
| **F7** | `local` | Parakeet | none (raw transcript) | none |
| **Ctrl+F7** | `dictate` | Parakeet | Gemini cleanup | OCR/selection |
| **Shift+F7** | `command` | Parakeet | Gemini acts on instruction | OCR/selection |
| **Alt+F7** | `multilingual` | audio → Gemini | Gemini transcribe+translate → English | OCR/selection/screenshot |

`local` is instant and fully offline. The others call Gemini through `pi`
(`multilingual` calls the Gemini REST API directly because `pi` can't attach
audio). On a cloud failure, `dictate` falls back to the raw transcript;
`command`/`multilingual` type nothing but raise a desktop notification — **never a
silent failure**.

### Activation
- **Hold** the key to talk; **release** to commit (push-to-talk).
- **Double-tap** (two quick taps) to **lock** hands-free listening; tap once more to
  stop and commit. The mode is captured on the first tap and persists.

## Configuration — `config.toml`

Generated from `config.toml.tmpl`. Edit the template in the chezmoi source, then
`chezmoi apply ~/.config/voice-typer/config.toml` and restart the daemon
(`systemctl --user restart voice-typerd.service`).

### `[model]` — the smart layer (dictate/command/multilingual)
| Key | Default | Meaning |
|-----|---------|---------|
| `name` | `google/gemini-2.5-flash` | `pi` model in `provider/id` form. Needs the matching API key in `~/.secrets` (e.g. `GEMINI_API_KEY`). |
| `thinking` | `off` | Reasoning effort: `off`/`minimal`/`low`/`medium`/`high`. |

### `[stt]` — Parakeet
| Key | Default | Meaning |
|-----|---------|---------|
| `device` | `""` | Input device substring; empty = system default source (e.g. Jabra). |
| `model_dir` | `""` | Parakeet model dir; empty = its default. |
| `silence_ms` | `1500` | Silence (ms) that ends an utterance in locked/continuous mode. |
| `vad_threshold` | `0.5` | Voice-activity-detection sensitivity. |
| `idle_shutdown_secs` | `900` | Unload the warm model after this many idle seconds (`0` = never). |
| `prewarm` | `false` | Load the model when the daemon starts instead of on first use. |

### `[activation]`
| Key | Default | Meaning |
|-----|---------|---------|
| `tap_ms` | `250` | A hold shorter than this counts as a tap (double-tap candidate). |
| `double_tap_ms` | `350` | Window to detect the second tap → lock. |
| `commit_timeout_secs` | `12` | How long to wait for a transcript after you stop. |

### `[context]` — what the smart layer sees
| Key | Default | Meaning |
|-----|---------|---------|
| `screen_context` | `ocr` | `ocr` (tesseract of the active window, cheap/private), `screenshot` (image → vision model), or `none`. |
| `ocr_lang` | `eng` | tesseract language. |
| `ocr_max_chars` | `6000` | Cap on OCR text length. |
| `screenshot_active_window` | `true` | Capture only the active window (Linux/grim). |
| `screenshot_max_width` | `1200` | Downscale width for screenshot mode (`0` = full PNG). |
| `send_selection` | `true` | Include the primary selection as context. |

Context is **reference-only** (used to fix spelling of on-screen names); the system
prompts forbid the model from echoing it.

### `[output]`
| Key | Default | Meaning |
|-----|---------|---------|
| `keep_on_clipboard` | `true` | Leave the produced text on the clipboard after typing. |

### `[audio]` — while recording
| Key | Default | Meaning |
|-----|---------|---------|
| `duck_while_recording` | `true` | Lower the default sink (music) while you talk. |
| `duck_volume` | `0.1` | Ducked level (fraction of original). |
| `boost_mic_while_recording` | `true` | Raise the mic (default source) while recording. |
| `mic_boost_volume` | `1.0` | Mic level while recording (`1.0` = 100%; >1 can clip). |

Applies to **all** modes; restored on commit.

### `[multilingual]` — Alt+F7 audio upload (needs ffmpeg)
The recording is normalized before upload: downsampled to 16 kHz mono (Gemini
downsamples anyway — ~6× smaller) and long pauses are trimmed.
| Key | Default | Meaning |
|-----|---------|---------|
| `preprocess` | `true` | Normalize/trim with ffmpeg before upload (falls back to the raw WAV if ffmpeg is missing). |
| `trim_silence` | `true` | Remove long silent gaps. |
| `silence_threshold_db` | `-40` | dBFS below which audio counts as silence. Less negative (e.g. `-35`) = more aggressive; the boosted-Jabra noise floor sits ~-35. |
| `silence_min_secs` | `1.0` | Only collapse gaps at least this long (keeps natural pauses). |

### `[debug]`
| Key | Default | Meaning |
|-----|---------|---------|
| `save_recordings` | `true` | Save the last mic capture to `~/.cache/voice-typer/last-recording.wav` for playback (`pw-play`). Multilingual always saves it (it needs the WAV). |

### `[hud]`
| Key | Default | Meaning |
|-----|---------|---------|
| `enabled` | `true` | Show the quickshell HUD. Auto-disables if `qs` is absent. |

### `[commands]` — platform tools (argv arrays; `{text}`/`{path}` substituted)
Per-OS (Linux vs macOS) in the template. Linux defaults: `screenshot=grim`,
`window_info=hyprctl activewindow -j`, `type_text=wtype -s 120 -d 8 -- {text}`,
`copy=wl-copy`, `paste_primary=wl-paste --primary --no-newline`.
- `type_text` `-s 120` = wait after creating the virtual keyboard so the first key
  isn't dropped; `-d 8` = ~70 chars/s so a fast burst doesn't overrun the terminal
  pipe. Raise/lower if a leading char is dropped or typing feels slow.

## System prompts (you can edit these)
- `smart-transcriber.system.md` — dictation cleanup (Ctrl+F7).
- `smart-command.system.md` — command/action (Shift+F7).
- `smart-translate.system.md` — multilingual → English (Alt+F7).

All resolve spoken self-corrections ("no, I mean X not Y" → types X) and never
answer/echo the context.

## Files
| File | Role |
|------|------|
| `voice-typerd.py` | Orchestrator daemon (state machine, engine, context, output, audio, modes). |
| `voice-ctl` | Tiny client: `voice-ctl {down\|up\|toggle} [local\|dictate\|command\|multilingual]`. |
| `config.toml` | This config (generated from `config.toml.tmpl`). |
| `smart-*.system.md` | The three system prompts. |
| `cava-mic` + `cava-mic.conf` | HUD mic-spectrum equalizer. |
| HUD | `~/.config/quickshell/voice/` (separate quickshell instance, IPC target `voice`). |

## Service & logs
Runs as a user service: `systemctl --user {status,restart} voice-typerd.service`.
Logs: `journalctl --user -u voice-typerd.service -f` (shows `local/output/command/
multilingual ->`, `audio preprocess`, duck/boost, failures). The daemon auto-starts
on the first hotkey if not already running.

## Dependencies
`parakeet-cli` (+ model via `parakeet download`), `pi`, `wtype`, `wl-clipboard`,
`grim`, `tesseract`(+`tesseract-data-eng`), `ffmpeg`, `cava`, `imagemagick`,
`quickshell`, `libnotify`, PipeWire (`pw-record`/`wpctl`). All in the chezmoi Arch
installer. macOS support is in progress (see the port note in the thoughts repo).
