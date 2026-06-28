-- DR-001: Alt is the primary Hyprland window-management modifier.
-- DR-002: macOS Option app chords move to Super on Linux.
local mainMod = "ALT"
local secMod = "SUPER"
local HYPRSCRIPTS = "~/.config/hypr/scripts"

-- Applications
hl.bind(mainMod .. " + RETURN", hl.dsp.exec_cmd("ghostty -e herdr"), { description = "Open Herdr" })
hl.bind(mainMod .. " + SHIFT + RETURN", hl.dsp.exec_cmd("ghostty -e herdr --remote dev-hub --remote-keybindings local"),
    { description = "Open remote Herdr" })
hl.bind(secMod .. " + B", hl.dsp.exec_cmd("zen-browser"), { description = "Open browser" })
hl.bind(secMod .. " + T", hl.dsp.exec_cmd("Telegram"), { description = "Open Telegram" })
hl.bind(secMod .. " + O", hl.dsp.exec_cmd("obsidian"), { description = "Open Obsidian" })
hl.bind(secMod .. " + E", hl.dsp.exec_cmd("thunar"), { description = "Open file manager" })
hl.bind(mainMod .. " + CTRL + E", hl.dsp.exec_cmd("walker -m unicode"), { description = "Open emoji picker" })
hl.bind(mainMod .. " + CTRL + C", hl.dsp.exec_cmd("walker -m calc"), { description = "Open calculator" })
hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd("walker"), { description = "Open launcher" })
hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd("walker -m clipboard"), { description = "Open clipboard history" })
hl.bind(secMod .. " + K", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/keybindings.sh"), { description = "Show keybindings" })

-- Clipboard & editing (mac-style system-wide chords)
-- ALT+C/X/V/A/Z + ALT+SHIFT+Z -> copy/cut/paste/select-all/undo/redo. In GUI
-- apps these send the Ctrl-based equivalent; in terminals copy/paste re-send the
-- Alt chord (Ghostty handles them) and the rest are no-ops (Ctrl+C=SIGINT,
-- Ctrl+Z=suspend, etc). See scripts/smart-clipboard.sh.
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/smart-clipboard.sh copy"),
    { description = "Copy (system-wide)" })
hl.bind(mainMod .. " + X", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/smart-clipboard.sh cut"),
    { description = "Cut (system-wide)" })
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/smart-clipboard.sh paste"),
    { description = "Paste (system-wide)" })
hl.bind(mainMod .. " + A", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/smart-clipboard.sh selectall"),
    { description = "Select all (system-wide)" })
hl.bind(mainMod .. " + Z", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/smart-clipboard.sh undo"),
    { description = "Undo (system-wide)" })
hl.bind(mainMod .. " + SHIFT + Z", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/smart-clipboard.sh redo"),
    { description = "Redo (system-wide)" })

-- Windows
hl.bind(mainMod .. " + Q", hl.dsp.window.close(), { description = "Close active window" })
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.exec_cmd("hyprctl activewindow -j | jq -r '.pid' | xargs -r kill"),
    { description = "Kill active window process" })
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }),
    { description = "Toggle fullscreen" })
hl.bind(mainMod .. " + M", hl.dsp.window.float({ action = "toggle" }), { description = "Toggle floating" })
hl.bind(mainMod .. " + left", hl.dsp.focus({ direction = "left" }), { description = "Move focus left" })
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }), { description = "Move focus right" })
hl.bind(mainMod .. " + up", hl.dsp.focus({ direction = "up" }), { description = "Move focus up" })
hl.bind(mainMod .. " + down", hl.dsp.focus({ direction = "down" }), { description = "Move focus down" })
-- ALT+H/J/L (focus) intentionally freed for in-app shortcuts; use ALT+arrows to move focus.
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true, description = "Move window with the mouse" })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true, description = "Resize window with the mouse" })
hl.bind(mainMod .. " + " .. secMod .. " + right", hl.dsp.window.resize({ x = 100, y = 0, relative = true }),
    { repeating = true, description = "Increase window width with keyboard" })
hl.bind(mainMod .. " + " .. secMod .. " + left", hl.dsp.window.resize({ x = -100, y = 0, relative = true }),
    { repeating = true, description = "Reduce window width with keyboard" })
hl.bind(mainMod .. " + " .. secMod .. " + down", hl.dsp.window.resize({ x = 0, y = 100, relative = true }),
    { repeating = true, description = "Increase window height with keyboard" })
hl.bind(mainMod .. " + " .. secMod .. " + up", hl.dsp.window.resize({ x = 0, y = -100, relative = true }),
    { repeating = true, description = "Reduce window height with keyboard" })
hl.bind(mainMod .. " + " .. secMod .. " + L", hl.dsp.window.resize({ x = 100, y = 0, relative = true }),
    { repeating = true, description = "Increase window width with keyboard" })
hl.bind(mainMod .. " + " .. secMod .. " + H", hl.dsp.window.resize({ x = -100, y = 0, relative = true }),
    { repeating = true, description = "Reduce window width with keyboard" })
hl.bind(mainMod .. " + " .. secMod .. " + J", hl.dsp.window.resize({ x = 0, y = 100, relative = true }),
    { repeating = true, description = "Increase window height with keyboard" })
hl.bind(mainMod .. " + " .. secMod .. " + K", hl.dsp.window.resize({ x = 0, y = -100, relative = true }),
    { repeating = true, description = "Reduce window height with keyboard" })
hl.bind(mainMod .. " + SHIFT + left", hl.dsp.window.swap({ direction = "l" }), { description = "Swap tiled window left" })
hl.bind(mainMod .. " + SHIFT + right", hl.dsp.window.swap({ direction = "r" }),
    { description = "Swap tiled window right" })
hl.bind(mainMod .. " + SHIFT + up", hl.dsp.window.swap({ direction = "u" }), { description = "Swap tiled window up" })
hl.bind(mainMod .. " + SHIFT + down", hl.dsp.window.swap({ direction = "d" }), { description = "Swap tiled window down" })
hl.bind(mainMod .. " + SHIFT + H", hl.dsp.window.swap({ direction = "l" }), { description = "Swap tiled window left" })
hl.bind(mainMod .. " + SHIFT + J", hl.dsp.window.swap({ direction = "d" }), { description = "Swap tiled window down" })
hl.bind(mainMod .. " + SHIFT + K", hl.dsp.window.swap({ direction = "u" }), { description = "Swap tiled window up" })
hl.bind(mainMod .. " + SHIFT + L", hl.dsp.window.swap({ direction = "r" }), { description = "Swap tiled window right" })
hl.bind(secMod .. " + Tab", hl.dsp.window.cycle_next(),
    { repeating = true, description = "Cycle between windows" })
hl.bind(secMod .. " + Tab", hl.dsp.window.bring_to_top(),
    { repeating = true, description = "Bring active window to the top" })

-- Actions
hl.bind(mainMod .. " + CTRL + R", hl.dsp.exec_cmd("hyprctl reload"), { description = "Reload Hyprland configuration" })
-- ALT+SHIFT+D intentionally left UNBOUND so Ghostty passes it through to Herdr,
-- which maps alt+shift+d -> split_horizontal. The old "toggle animations" action
-- (HYPRSCRIPTS/toggle-animations.sh) lived here; rebind it to a free chord if wanted.
hl.bind("CTRL + PRINT", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/screenshot.sh"), { description = "Take a screenshot" })

-- Voice dictation (voice-typer): hold to talk (release sends); double-tap to lock
-- hands-free listening, press again to commit. See ~/.config/voice-typer.
--   F7        = local only — Parakeet transcript typed verbatim (instant, offline)
--   CTRL+F7   = dictation — Parakeet -> Gemini cleanup (OCR + selection context)
--   SHIFT+F7  = command   — Gemini acts on the spoken instruction, types the result
--   ALT+F7    = multilingual — speak Iraqi Arabic and/or English -> English (audio -> Gemini)
--   CTRL+ALT+V = re-type the LAST dictation from disk (no clipboard; survives a clipboard miss)
-- (Mac will map CMD+F7 to multilingual.)
local VOICE_CTL = "~/.config/voice-typer/voice-ctl"
hl.bind("F7", hl.dsp.exec_cmd(VOICE_CTL .. " down local"), { description = "Voice dictation local (push-to-talk)" })
hl.bind("F7", hl.dsp.exec_cmd(VOICE_CTL .. " up local"), { release = true, description = "Voice dictation local (release)" })
hl.bind("CTRL + F7", hl.dsp.exec_cmd(VOICE_CTL .. " down dictate"), { description = "Voice dictation + AI cleanup (push-to-talk)" })
hl.bind("CTRL + F7", hl.dsp.exec_cmd(VOICE_CTL .. " up dictate"), { release = true, description = "Voice dictation + AI cleanup (release)" })
hl.bind("SHIFT + F7", hl.dsp.exec_cmd(VOICE_CTL .. " down command"), { description = "Voice command (push-to-talk)" })
hl.bind("SHIFT + F7", hl.dsp.exec_cmd(VOICE_CTL .. " up command"), { release = true, description = "Voice command (release/run)" })
hl.bind("ALT + F7", hl.dsp.exec_cmd(VOICE_CTL .. " down multilingual"), { description = "Voice multilingual -> English (push-to-talk)" })
hl.bind("ALT + F7", hl.dsp.exec_cmd(VOICE_CTL .. " up multilingual"), { release = true, description = "Voice multilingual (release)" })
-- Re-type the last dictation from ~/.cache/voice-typer/last-response.txt straight via
-- wtype (no clipboard). release-bind so CTRL+ALT have lifted before the daemon types.
hl.bind("CTRL + ALT + V", hl.dsp.exec_cmd(VOICE_CTL .. " paste-last"), { release = true, description = "Voice: re-type last dictation (wtype, no clipboard)" })
hl.bind(mainMod .. " + " .. secMod .. " + G", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/gamemode.sh"),
    { description = "Toggle game mode" })
hl.bind(mainMod .. " + CTRL + Q", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/wlogout.sh"), { description = "Open power menu" })
hl.bind(mainMod .. " + SHIFT + W", hl.dsp.exec_cmd("~/.config/theme-system/scripts/wallpaper-manager.py random"),
    { description = "Set random wallpaper" })
hl.bind(mainMod .. " + CTRL + W",
    hl.dsp.exec_cmd("qs -p ~/.config/quickshell/wallpaper ipc call wallpaper toggle"),
    { description = "Toggle wallpaper panel" })
hl.bind(mainMod .. " + " .. secMod .. " + W", hl.dsp.exec_cmd(HYPRSCRIPTS .. "/wallpaper.sh automation"),
    { description = "Toggle random wallpaper automation" })
hl.bind(secMod .. " + L", hl.dsp.exec_cmd("~/.config/hypr/scripts/power.sh lock"),
    { description = "Lock screen" })

-- Workspaces
for i = 1, 10 do
    local key = i % 10
    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i }), { description = "Focus workspace " .. i })
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }),
        { description = "Move window to workspace " .. i })
    hl.bind(mainMod .. " + " .. secMod .. " + " .. key, hl.dsp.exec_cmd(HYPRSCRIPTS .. "/moveTo.sh " .. i),
        { description = "Move all windows to workspace " .. i .. " and follow" })
end

hl.bind(mainMod .. " + Tab", hl.dsp.focus({ workspace = "m+1" }), { description = "Open next workspace" })
hl.bind(mainMod .. " + SHIFT + Tab", hl.dsp.focus({ workspace = "m-1" }), { description = "Open previous workspace" })
hl.bind(mainMod .. " + SHIFT + F", hl.dsp.workspace.move({ monitor = "r" }),
    { description = "Move current workspace to next monitor" })
hl.bind(mainMod .. " + SHIFT + A", hl.dsp.workspace.move({ monitor = "l" }),
    { description = "Move current workspace to previous monitor" })
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }), { description = "Open next workspace" })
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }), { description = "Open previous workspace" })
hl.bind(mainMod .. " + CTRL + down", hl.dsp.focus({ workspace = "empty" }),
    { description = "Open the next empty workspace" })

-- Fn keys
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -q s +10%"),
    { locked = true, repeating = true, description = "Increase brightness by 10%" })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -q s 10%-"),
    { locked = true, repeating = true, description = "Reduce brightness by 10%" })
hl.bind("XF86AudioRaiseVolume",
    hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 && wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 5%+"),
    { locked = true, repeating = true, description = "Increase volume by 5%" })
hl.bind("XF86AudioLowerVolume",
    hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 && wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),
    { locked = true, repeating = true, description = "Reduce volume by 5%" })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),
    { locked = true, description = "Toggle mute" })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true, description = "Audio play pause" })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl pause"), { locked = true, description = "Audio pause" })
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true, description = "Audio next" })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true, description = "Audio previous" })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),
    { locked = true, description = "Toggle microphone" })
hl.bind("XF86Calculator", hl.dsp.exec_cmd("gnome-calculator"),
    { locked = true, description = "Open calculator" })
hl.bind("XF86ScreenSaver", hl.dsp.exec_cmd("hyprlock"), { locked = true, description = "Open screenlock" })
