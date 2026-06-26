//@ pragma UseQApplication
// WIP top bar — mirrors the macOS SketchyBar look (floating, rounded, accent border).
// Owned locally; will be migrated into chezmoi once we're happy with it.
// Run:  qs -p ~/.config/quickshell/bar
// Tall window + input mask so tooltips render below the bar; bar strip is the only
// interactive region. Reuses ML4W's Quickshell calendar/power popups via IPC.

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Services.SystemTray
import Quickshell.Services.Mpris
import Quickshell.Widgets
import Qt5Compat.GraphicalEffects

ShellRoot {
    id: root

    // ---- Theme tokens (overwritten from colors.json when available) ----
    property color cBg: "#1a1110"
    property color cPrimary: "#ffb4a5"
    property color cOnSurface: "#f1dfdb"
    property color cOutline: "#a08c88"
    property color cError: "#ffb4ab"
    // Extra Material Design 3 roles used by the theme-control popup. These have
    // sensible fallbacks derived from the core four, overwritten from colors.json
    // when the theme-system emits them.
    property color cOnPrimary: "#3b0b03"
    property color cSecondary: cPrimary
    property color cTertiary: cPrimary
    property color cSurface: Qt.lighter(cBg, 1.35)
    property color cSurfaceHigh: Qt.lighter(cBg, 1.7)
    property color cPrimaryContainer: Qt.rgba(cPrimary.r, cPrimary.g, cPrimary.b, 0.16)

    readonly property int barHeight: 50
    readonly property int topGap: 8
    readonly property int sideMargin: 15
    readonly property int popupRoom: 220
    readonly property int barBorderWidth: 2
    readonly property string uiFont: "JetBrainsMono Nerd Font"
    readonly property string numFont: "ttyclock"
    readonly property string scriptDir: Quickshell.env("HOME") + "/.config/quickshell/bar/scripts/"
    readonly property string themeMgr: Quickshell.env("HOME") + "/.config/theme-system/scripts/theme-manager.py"
    readonly property string wallMgr: Quickshell.env("HOME") + "/.config/theme-system/scripts/wallpaper-manager.py"

    // Tray icons whose id/title/tooltip contains any of these render UNtinted — full-color
    // app icons the accent ColorOverlay would otherwise flatten into a solid square (e.g. Tailscale).
    readonly property var trayNoTint: ["tailscale"]

    property string focusedTitle: ""    // full un-elided title (for tooltip)
    property string focusedClass: ""    // window class (for tooltip)
    property int focusedPid: 0          // PID (for tooltip)
    // bar display: full title, falling back to class (derived from focused* above)
    readonly property string focusedApp: focusedTitle || focusedClass
    property bool procOpen: false
    property string procFilter: "cpu"  // "cpu" or "mem"
    property real procClickX: 0        // monitor-relative center-x of the stat that opened the proc popup
    property string procScreen: ""     // name of the monitor the proc popup opened on (latched at open)
    property var wsWindows: ({})       // { "1": [{cls:"kitty",n:7}, {cls:"zen",n:1}], ... }
    property int notifCount: 0         // unseen notifications (swaync)
    property bool notifHas: false      // unseen notifications present
    property bool notifDnd: false      // do-not-disturb on
    property int updateCount: 0        // pending system updates (our scripts/updates.sh)
    property string updateTip: ""      // "<repo> official · <aur> AUR"
    property bool updListOpen: false   // updates-list popup open (right-click)
    property real updListX: 0          // monitor-relative center-x of the updates widget
    property string updListScreen: ""  // screen the updates popup opened on (latched)
    property bool updLoading: false    // updates list is being fetched (shows "checking…")

    // ---- media (MPRIS) ----
    property bool mediaOpen: false      // media controls popup open
    property real mediaX: 0             // monitor-relative center-x of the now-playing widget
    property string mediaScreen: ""     // screen the media popup opened on (latched)
    property int mediaSel: -1           // -1 = auto-pick active player; >=0 = user-chosen index
    property real mediaPos: 0           // polled playback position (s) driving the popup progress
    // De-duplicate playerctld (it mirrors whatever is active) unless it's all we have.
    readonly property var mediaPlayers: {
        const all = Mpris.players.values || [];
        const f = all.filter(p => (p.identity || "").toLowerCase() !== "playerctld"
                              && ("" + p.dbusName).toLowerCase().indexOf("playerctld") < 0);
        return f.length > 0 ? f : all;
    }
    // Chosen player: explicit user selection, else the first playing, else the first.
    readonly property var player: {
        const ps = root.mediaPlayers;
        if (!ps || ps.length === 0) return null;
        if (root.mediaSel >= 0 && root.mediaSel < ps.length) return ps[root.mediaSel];
        for (let i = 0; i < ps.length; i++) if (ps[i].isPlaying) return ps[i];
        return ps[0];
    }
    function cyclePlayer() {
        const n = root.mediaPlayers.length;
        if (n <= 1) return;
        const cur = root.mediaSel >= 0 ? root.mediaSel : root.mediaPlayers.indexOf(root.player);
        root.mediaSel = ((cur < 0 ? 0 : cur) + 1) % n;
    }
    function cycleLoop() {
        if (!root.player || !root.player.loopSupported) return;
        const s = root.player.loopState;
        root.player.loopState = (s === MprisLoopState.None) ? MprisLoopState.Playlist
                              : (s === MprisLoopState.Playlist) ? MprisLoopState.Track
                              : MprisLoopState.None;
    }
    function fmtTime(s) {
        if (!s || s < 0 || !isFinite(s)) return "0:00";
        s = Math.floor(s);
        const m = Math.floor(s / 60);
        const ss = s % 60;
        return m + ":" + (ss < 10 ? "0" : "") + ss;
    }
    // Poll position only while the popup is open and actually playing.
    Timer {
        interval: 500; repeat: true; triggeredOnStart: true
        running: root.mediaOpen && root.player !== null && root.player.isPlaying
        onTriggered: root.mediaPos = root.player ? root.player.position : 0
    }

    // Clamped left margin to horizontally center a popup of width `w` under `item`,
    // keeping it within winWidth (the full-width bar).
    function popupLeft(item, winWidth, w) {
        // mapToItem(null, ...) = window/monitor-relative x (screen-agnostic).
        // mapToGlobal would add the monitor's global offset and pin the popup to
        // the right edge on any non-primary screen.
        const cx = item.mapToItem(null, item.width / 2, 0).x;
        const left = Math.round(cx - w / 2);       // center the popup under the click
        return Math.max(0, Math.min(left, winWidth - w));
    }


    // Switch to the focused monitor's active workspace ± delta, clamped to the 1–9 the bar shows.
    function switchWorkspaceRel(delta) {
        const cur = Hyprland.focusedMonitor?.activeWorkspace?.id ?? 1;
        let t = cur + delta;
        if (t < 1) t = 1; else if (t > 9) t = 9;
        if (t === cur) return;
        if (Hyprland.usingLua)
            Hyprland.dispatch("hl.dsp.focus({workspace = '" + t + "'})");
        else
            Hyprland.dispatch("workspace " + t);
    }

    Process {
        id: colorReader
        command: ["bash", "-c", "cat \"$HOME/.config/quickshell/bar/colors.json\""]
        running: true
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const j = JSON.parse(this.text.trim());
                    if (j.background)  root.cBg = j.background;
                    if (j.primary)     root.cPrimary = j.primary;
                    if (j.on_surface)  root.cOnSurface = j.on_surface;
                    if (j.outline)     root.cOutline = j.outline;
                    if (j.on_primary)  root.cOnPrimary = j.on_primary;
                    if (j.secondary)   root.cSecondary = j.secondary;
                    if (j.tertiary)    root.cTertiary = j.tertiary;
                    if (j.error)       root.cError = j.error;
                    if (j.surface_container)      root.cSurface = j.surface_container;
                    if (j.surface_container_high) root.cSurfaceHigh = j.surface_container_high;
                    if (j.primary_container)      root.cPrimaryContainer = j.primary_container;
                } catch (e) { /* keep fallbacks */ }
            }
        }
    }

    Process {
        id: appProc
        command: ["hyprctl", "activewindow", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const w = JSON.parse(this.text.trim());
                    root.focusedTitle = w.title || "";
                    root.focusedClass = w.class || "";
                    root.focusedPid = w.pid || 0;
                } catch (e) {
                    root.focusedTitle = "";
                    root.focusedClass = "";
                    root.focusedPid = 0;
                }
            }
        }
    }
    // Refreshed on Hyprland focus/title events (see Connections below). The timer is
    // just a safety net + initial population; the debounce collapses event bursts.
    Timer { id: appDebounce; interval: 80; onTriggered: appProc.running = true }
    Timer { interval: 30000; running: true; repeat: true; triggeredOnStart: true; onTriggered: appProc.running = true }

    // Workspace window list (for hover tooltips)
    Process {
        id: wsProc
        command: ["hyprctl", "clients", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const clients = JSON.parse(this.text.trim());
                    const map = {};
                    for (let i = 0; i < clients.length; i++) {
                        const c = clients[i];
                        const ws = "" + c.workspace.id;
                        const cls = c.class || c.title || "?";
                        if (!map[ws]) map[ws] = {};
                        map[ws][cls] = (map[ws][cls] || 0) + 1;
                    }
                    const out = {};
                    for (const ws in map) {
                        const arr = [];
                        for (const cls in map[ws])
                            arr.push({ cls: cls, n: map[ws][cls] });
                        arr.sort((a, b) => b.n - a.n);   // most instances first
                        out[ws] = arr;
                    }
                    root.wsWindows = out;
                } catch (e) { /* keep previous */ }
            }
        }
    }
    // Refresh on Hyprland window events (debounced) instead of steady 2s polling.
    Timer { id: wsDebounce; interval: 120; onTriggered: wsProc.running = true }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            switch (event.name) {
            case "openwindow": case "closewindow": case "movewindow":
            case "movewindowv2": case "windowtitle": case "windowtitlev2":
                wsDebounce.restart();
            }
            switch (event.name) {
            case "activewindow": case "activewindowv2":
            case "windowtitle": case "windowtitlev2":
            case "closewindow": case "focusedmon": case "focusedmonv2":
                appDebounce.restart();
            }
        }
    }
    // Safety net + initial population (also catches any events missed above).
    Timer { interval: 30000; running: true; repeat: true; triggeredOnStart: true; onTriggered: wsProc.running = true }

    // swaync notification state (streamed via -swb; drives the bell icon)
    Process {
        id: notifProc
        command: ["swaync-client", "-swb"]
        running: true
        stdout: SplitParser {
            onRead: (line) => {
                try {
                    const j = JSON.parse(line);
                    const alt = j.alt || "";
                    root.notifDnd = alt.indexOf("dnd") >= 0;
                    root.notifHas = alt.indexOf("notification") >= 0;
                    root.notifCount = parseInt(j.text) || 0;
                } catch (e) { /* ignore malformed line */ }
            }
        }
    }

    // Pending system updates — our own checker (no ML4W dependency). Polled every 30 min.
    Process {
        id: updateProc
        command: ["bash", root.scriptDir + "updates.sh"]
        stdout: StdioCollector {
            onStreamFinished: {
                const t = this.text.trim();
                const i = t.indexOf("|");
                root.updateCount = parseInt(i >= 0 ? t.slice(0, i) : t) || 0;
                root.updateTip = i >= 0 ? t.slice(i + 1) : "";
            }
        }
    }
    Timer { interval: 300000; running: true; repeat: true; triggeredOnStart: true; onTriggered: updateProc.running = true }

    // Detailed pending-updates list (for the right-click popup).
    ListModel { id: updModel }
    Process {
        id: updListProc
        command: ["bash", root.scriptDir + "updates.sh", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                const lines = this.text.trim().split("\n").filter(l => l.length > 0);
                let row = 0, repo = 0, aur = 0, flat = 0;
                for (let i = 0; i < lines.length; i++) {
                    const p = lines[i].split(" ");
                    if (p.length < 4) continue;
                    const e = { name: p[0], oldv: p[1], newv: p[2], src: p[3] };
                    if (row < updModel.count) updModel.set(row, e);
                    else updModel.append(e);
                    if (p[3] === "repo") repo++; else if (p[3] === "aur") aur++; else flat++;
                    row++;
                }
                while (updModel.count > row) updModel.remove(updModel.count - 1);
                // keep the badge in sync with the freshly-fetched list
                root.updateCount = row;
                root.updateTip = repo + " official · " + aur + " AUR · " + flat + " flatpak";
                root.updLoading = false;
            }
        }
    }

    ListModel { id: procModel }

    Process {
        id: procRefresh
        command: ["bash", root.scriptDir + "topprocs.sh", root.procFilter]
        stdout: StdioCollector {
            onStreamFinished: {
                // Update rows in place (set/append/trim) so delegates aren't destroyed
                // and recreated every refresh — avoids flicker and hover-state loss.
                const lines = this.text.trim().split("\n").filter(l => l.length > 0);
                let row = 0;
                for (let i = 0; i < lines.length; i++) {
                    const p = lines[i].split(" ");
                    if (p.length < 4) continue;
                    const entry = { pid: p[0], cpu: parseFloat(p[1]), mem: parseFloat(p[2]), cmd: p.slice(3).join(" ") };
                    if (row < procModel.count) procModel.set(row, entry);
                    else procModel.append(entry);
                    row++;
                }
                while (procModel.count > row) procModel.remove(procModel.count - 1);
            }
        }
    }

    // System stat values — polled once at root (shared by all monitors) instead of
    // once per monitor's Stat. cpu/mem share a 2s timer; others keep their cadence.
    property string cpuRaw: "··"
    property string memRaw: "··"
    property string diskRaw: "··"
    property string volRaw: "··"
    property string netRaw: "··"
    Process { id: cpuProc;  command: ["bash", root.scriptDir + "cpu.sh"];  stdout: StdioCollector { onStreamFinished: root.cpuRaw  = this.text.trim() } }
    Process { id: memProc;  command: ["bash", root.scriptDir + "mem.sh"];  stdout: StdioCollector { onStreamFinished: root.memRaw  = this.text.trim() } }
    Process { id: diskProc; command: ["bash", root.scriptDir + "disk.sh"]; stdout: StdioCollector { onStreamFinished: root.diskRaw = this.text.trim() } }
    Process { id: volProc;  command: ["bash", root.scriptDir + "vol.sh"];  stdout: StdioCollector { onStreamFinished: root.volRaw  = this.text.trim() } }
    Process { id: netProc;  command: ["bash", root.scriptDir + "net.sh"];  stdout: StdioCollector { onStreamFinished: root.netRaw  = this.text.trim() } }
    Timer { interval: 2000;  running: true; repeat: true; triggeredOnStart: true; onTriggered: { cpuProc.running = true; memProc.running = true } }
    Timer { interval: 1000;  running: true; repeat: true; triggeredOnStart: true; onTriggered: volProc.running = true }
    Timer { id: volRefreshSoon; interval: 80; onTriggered: volProc.running = true }  // snappy re-read after a scroll
    Timer { interval: 5000;  running: true; repeat: true; triggeredOnStart: true; onTriggered: netProc.running = true }
    Timer { interval: 30000; running: true; repeat: true; triggeredOnStart: true; onTriggered: diskProc.running = true }

    // External control of the process popup. Single handler at root — was previously
    // duplicated per-monitor by Variants (logged a "another handler is registered" warning).
    IpcHandler {
        target: "procmon"
        function toggle(): void {
            if (root.procOpen) { root.procOpen = false; return; }
            root.procScreen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
            root.procOpen = true;
        }
        function open(): void {
            root.procScreen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
            root.procOpen = true;
        }
        function close(): void { root.procOpen = false }
    }

    // ---- Theme control (parity with the macOS SketchyBar theme menu) ----
    property bool themeOpen: false
    property real themeX: 0             // monitor-relative center-x of the trigger
    property string themeScreen: ""     // screen the popup opened on (latched)
    // Parsed live theme state (from .chezmoidata/theme.yaml).
    property string thName: "mocha"     // mocha | latte | frappe | macchiato | dynamic
    property string thVariant: "dark"   // dark | light
    property int    thOpacity: 100      // 0–100
    property real   thContrast: 0.0     // -1.0 … 1.0 (dynamic only)
    readonly property bool thDynamic: thName === "dynamic"
    readonly property bool thLight: thVariant === "light"
    readonly property bool themeBusy: themeAction.running
    readonly property string thPretty:
        thDynamic ? "Dynamic" : (thName.charAt(0).toUpperCase() + thName.slice(1))

    // Read current theme state straight from the chezmoi source (same source of
    // truth the SketchyBar plugins grep). Refreshed when the popup opens and
    // after every action completes.
    Process {
        id: themeStateProc
        command: ["bash", "-c", "cat \"$(chezmoi source-path 2>/dev/null)/.chezmoidata/theme.yaml\" 2>/dev/null"]
        running: true   // populate thOpacity/thName at startup (drives bar opacity)
        stdout: StdioCollector {
            onStreamFinished: {
                const t = this.text;
                const grab = (re, def) => { const m = t.match(re); return m ? m[1] : def; };
                root.thName    = grab(/\n\s*name:\s*["']?([A-Za-z0-9_]+)/, root.thName);
                root.thVariant = grab(/\n\s*variant:\s*["']?([A-Za-z]+)/, root.thVariant);
                root.thOpacity = parseInt(grab(/\n\s*opacity:\s*([0-9]+)/, "" + root.thOpacity));
                root.thContrast = parseFloat(grab(/\n\s*contrast:\s*([-0-9.]+)/, "" + root.thContrast));
            }
        }
    }

    // Runs theme-manager.py / wallpaper-manager.py. One at a time (themeBusy),
    // so we never trip the theme-manager lock file. On completion we re-read the
    // state and the bar's own colors (the plugin also pokes us via IPC).
    Process {
        id: themeAction
        stdout: StdioCollector { }
        stderr: StdioCollector { }
        onExited: (code, status) => {
            themeStateProc.running = true;
            colorReader.running = true;
            themeStateLater.restart();   // second pass once files have settled
        }
    }
    Timer { id: themeStateLater; interval: 600; onTriggered: themeStateProc.running = true }

    // Push the current theme to the devbox (theme-manager push). Kept separate
    // from themeAction so the Push button shows its own transient status.
    property string pushState: ""   // "" | "busy" | "ok" | "fail"
    Process {
        id: pushProc
        stdout: StdioCollector { }
        stderr: StdioCollector { }
        onExited: (code, status) => {
            root.pushState = (code === 0) ? "ok" : "fail";
            pushClear.restart();
        }
    }
    Timer { id: pushClear; interval: 2600; onTriggered: root.pushState = "" }
    function pushTheme() {
        if (pushProc.running) return;
        root.pushState = "busy";
        pushProc.command = ["bash", "-c",
            "export PATH=\"$HOME/.cargo/bin:$HOME/.local/bin:$PATH\"; exec uv run '" + root.themeMgr + "' push"];
        pushProc.running = true;
    }

    // Run a theme-system script via `uv run` (honors its inline PEP 723 deps).
    // We prepend ~/.cargo/bin + ~/.local/bin to PATH — exactly like the macOS
    // SketchyBar plugins — so matugen/uv resolve regardless of the compositor's
    // minimal environment.
    function runScript(script, args) {
        if (themeAction.running) return;   // ignore taps while one is in flight
        const q = (s) => "'" + ("" + s).replace(/'/g, "'\\''") + "'";
        let cmd = "export PATH=\"$HOME/.cargo/bin:$HOME/.local/bin:$PATH\"; exec uv run " + q(script);
        for (let i = 0; i < args.length; i++)
            cmd += " " + q(args[i]);
        themeAction.command = ["bash", "-c", cmd];
        themeAction.running = true;
    }
    function setVariant(variant) {
        // optimistic UI; themeStateProc corrects after the command lands
        root.thName = variant;
        root.thVariant = (variant === "latte") ? "light" : "dark";
        runScript(root.themeMgr, ["set", "static", "--variant", variant]);
    }
    function setDynamic() {
        root.thName = "dynamic";
        runScript(root.themeMgr, ["set", "dynamic"]);
    }
    function setMode(mode) {
        root.thVariant = mode;
        if (!root.thDynamic) root.thName = (mode === "light") ? "latte" : "mocha";
        runScript(root.themeMgr, ["mode", mode]);
    }
    function setOpacity(pct) {
        root.thOpacity = pct;
        runScript(root.themeMgr, ["opacity", "" + pct]);
    }
    function setContrast(c) {
        root.thContrast = c;
        runScript(root.themeMgr, ["set", "dynamic", "-c", c.toFixed(2)]);
    }
    function randomWallpaper() {
        runScript(root.wallMgr, ["random"]);
    }

    function openThemeAt(centerX) {
        // only one popup owns the focus grab at a time
        root.procOpen = false;
        root.updListOpen = false;
        root.mediaOpen = false;
        root.themeX = centerX;
        root.themeScreen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
        themeStateProc.running = true;
        root.themeOpen = true;
    }

    // Lets the theme-system poke the bar to re-read colors after applying a theme.
    IpcHandler {
        target: "bar"
        function reload(): void { colorReader.running = true; themeStateProc.running = true }
    }
    // Lets a keybinding open the theme menu (centered on the focused monitor).
    IpcHandler {
        target: "theme"
        function toggle(): void {
            if (root.themeOpen) { root.themeOpen = false; return; }
            const w = Hyprland.focusedMonitor ? (Hyprland.focusedMonitor.width || 1920) : 1920;
            root.openThemeAt(w / 2);
        }
        function open(): void {
            const w = Hyprland.focusedMonitor ? (Hyprland.focusedMonitor.width || 1920) : 1920;
            root.openThemeAt(w / 2);
        }
        function close(): void { root.themeOpen = false }
    }

    // ---- Reusable building blocks ----

    component Sep: Text {
        Layout.alignment: Qt.AlignVCenter
        text: "│"; color: root.cOutline
        font.family: root.uiFont; font.pixelSize: 18
    }

    component Tip: ToolTip {
        id: tip
        padding: 11
        x: parent ? Math.round((parent.width - width) / 2) : 0
        y: parent ? parent.height + 6 : 0
        implicitWidth: tipLabel.implicitWidth + 2 * padding
        implicitHeight: tipLabel.implicitHeight + 2 * padding
        background: GradientBorder {
            darkColor: root.cOnPrimary
            brightColor: root.cPrimary
            fillColor: Qt.rgba(root.cBg.r, root.cBg.g, root.cBg.b, 0.97)
            borderWidth: 2
            radius: 10
        }
        contentItem: Text {
            id: tipLabel
            text: tip.text
            color: root.cOnSurface
            font.family: root.uiFont
            font.pixelSize: 13
            lineHeight: 1.3
            textFormat: Text.PlainText
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
        }
    }

    // Rich tooltip for a workspace pill: bold header + per-app rows with counts (capped).
    component WsTip: ToolTip {
        id: wt
        property int wsId: 0
        readonly property var apps: root.wsWindows["" + wt.wsId] || []
        readonly property int maxRows: 12
        padding: 11
        x: parent ? Math.round((parent.width - width) / 2) : 0
        y: parent ? parent.height + 6 : 0
        background: GradientBorder {
            darkColor: root.cOnPrimary
            brightColor: root.cPrimary
            fillColor: Qt.rgba(root.cBg.r, root.cBg.g, root.cBg.b, 0.97)
            borderWidth: 2
            radius: 10
        }
        contentItem: ColumnLayout {
            spacing: 3
            Text {
                text: "Workspace " + wt.wsId
                color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 13; font.bold: true
            }
            Rectangle {
                Layout.fillWidth: true; implicitHeight: 1
                color: root.cPrimary; opacity: 0.25; visible: wt.apps.length > 0
            }
            Text {
                visible: wt.apps.length === 0
                text: "— empty —"; color: root.cOnSurface; opacity: 0.5
                font.family: root.uiFont; font.pixelSize: 12; font.italic: true
            }
            Repeater {
                model: Math.min(wt.apps.length, wt.maxRows)
                RowLayout {
                    spacing: 6
                    Text {
                        text: wt.apps[index].cls; color: root.cOnSurface
                        font.family: root.uiFont; font.pixelSize: 12
                    }
                    Text {
                        visible: wt.apps[index].n > 1
                        text: "×" + wt.apps[index].n; color: root.cPrimary; opacity: 0.85
                        font.family: root.uiFont; font.pixelSize: 12; font.bold: true
                    }
                }
            }
            Text {
                visible: wt.apps.length > wt.maxRows
                text: "+" + (wt.apps.length - wt.maxRows) + " more…"
                color: root.cOnSurface; opacity: 0.5
                font.family: root.uiFont; font.pixelSize: 11; font.italic: true
            }
        }
    }

    // Rich tooltip for the focused app: full title + class/PID rows.
    component AppTip: ToolTip {
        id: at
        readonly property bool hasAny: root.focusedTitle !== "" || root.focusedClass !== "" || root.focusedPid > 0
        padding: 11
        x: parent ? Math.round((parent.width - width) / 2) : 0
        y: parent ? parent.height + 6 : 0
        background: GradientBorder {
            darkColor: root.cOnPrimary
            brightColor: root.cPrimary
            fillColor: Qt.rgba(root.cBg.r, root.cBg.g, root.cBg.b, 0.97)
            borderWidth: 2
            radius: 10
        }
        contentItem: ColumnLayout {
            spacing: 3
            // Full title (may be long)
            Text {
                visible: root.focusedTitle !== ""
                text: root.focusedTitle
                color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 13; font.bold: true
                wrapMode: Text.Wrap; Layout.maximumWidth: 380
            }
            // Divider between title and class/pid — only when both sides have content
            Rectangle {
                Layout.fillWidth: true; implicitHeight: 1
                color: root.cPrimary; opacity: 0.25
                visible: root.focusedTitle !== "" && (root.focusedClass !== "" || root.focusedPid > 0)
            }
            // Class row
            RowLayout {
                visible: root.focusedClass !== ""
                spacing: 6
                Text { text: "class"; color: root.cOnSurface; opacity: 0.5; font.family: root.uiFont; font.pixelSize: 12 }
                Text { text: root.focusedClass; color: root.cOnSurface; font.family: root.uiFont; font.pixelSize: 12; font.bold: true }
            }
            // PID row
            RowLayout {
                visible: root.focusedPid > 0
                spacing: 6
                Text { text: "pid"; color: root.cOnSurface; opacity: 0.5; font.family: root.uiFont; font.pixelSize: 12 }
                Text { text: "" + root.focusedPid; color: root.cOnSurface; font.family: root.uiFont; font.pixelSize: 12; font.bold: true }
            }
            // Hint
            Rectangle {
                Layout.fillWidth: true; implicitHeight: 1
                color: root.cPrimary; opacity: 0.15; visible: at.hasAny
            }
            Text {
                visible: at.hasAny
                text: "click to open htop"
                color: root.cOnSurface; opacity: 0.35
                font.family: root.uiFont; font.pixelSize: 11; font.italic: true
            }
        }
    }
    // optional click command or popup toggle
    component Stat: MouseArea {
        id: si
        property string icon: ""
        property string label: ""
        property string clickCmd: ""
        property string popupTarget: ""
        property string rightCmd: ""       // optional: run on right-click (e.g. mute toggle)
        property string scrollUpCmd: ""    // optional: run on wheel-up (e.g. volume +)
        property string scrollDownCmd: ""  // optional: run on wheel-down (e.g. volume −)
        signal acted()                     // fired after a right-click/scroll command (for a snappy re-read)
        property string raw: "··"          // bound by the caller to a root.*Raw poller value
        readonly property string value: si.raw.indexOf("|") >= 0 ? si.raw.slice(0, si.raw.indexOf("|")) : si.raw
        readonly property string tip: si.raw.indexOf("|") >= 0
            ? si.raw.slice(si.raw.indexOf("|") + 1)
            : (si.label !== "" ? si.label + ": " + si.value : si.value)
        Layout.alignment: Qt.AlignVCenter
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: (clickCmd !== "" || rightCmd !== "" || popupTarget !== "") ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: (mouse) => {
            if (mouse.button === Qt.RightButton) {
                if (si.rightCmd !== "") { Quickshell.execDetached(["bash", "-c", si.rightCmd]); si.acted(); }
                return;
            }
            if (popupTarget === "proc") {
                const f = si.icon === "󰻠" ? "cpu" : "mem";
                if (root.procOpen && root.procFilter === f) {
                    root.procOpen = false;                 // same metric → close
                } else {
                    root.procFilter = f;                   // open, or switch metric in place
                    root.procClickX = si.mapToItem(null, si.width / 2, 0).x;
                    root.procScreen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
                    procRefresh.running = true;
                    root.procOpen = true;
                }
            } else if (clickCmd !== "")
                Quickshell.execDetached(["bash", "-c", clickCmd]);
        }
        onWheel: (wheel) => {
            if (wheel.angleDelta.y > 0 && si.scrollUpCmd !== "") {
                Quickshell.execDetached(["bash", "-c", si.scrollUpCmd]);
                si.acted();
            } else if (wheel.angleDelta.y < 0 && si.scrollDownCmd !== "") {
                Quickshell.execDetached(["bash", "-c", si.scrollDownCmd]);
                si.acted();
            }
        }
        implicitWidth: srow.implicitWidth
        implicitHeight: srow.implicitHeight
        RowLayout {
            id: srow
            anchors.centerIn: parent
            spacing: 5
            Text { Layout.alignment: Qt.AlignVCenter; text: si.icon;  color: root.cPrimary; font.family: root.uiFont;  font.pixelSize: 16 }
            Text { Layout.alignment: Qt.AlignVCenter; text: si.value; color: root.cPrimary; font.family: root.numFont; font.pixelSize: 15 }
        }
        Tip { visible: si.containsMouse; text: si.tip }
    }

    // clickable glyph with tooltip and optional right-click
    component IconButton: Text {
        id: ib
        property string cmd: ""
        property string cmdRight: ""
        property string tip: ""
        signal tapped()                    // fired on left-click
        Layout.alignment: Qt.AlignVCenter
        color: root.cPrimary
        font.family: root.uiFont
        font.pixelSize: 18
        MouseArea {
            id: ibm
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: (mouse) => {
                if (mouse.button === Qt.RightButton) {
                    if (ib.cmdRight !== "") Quickshell.execDetached(["bash", "-c", ib.cmdRight]);
                } else {
                    if (ib.cmd !== "") Quickshell.execDetached(["bash", "-c", ib.cmd]);
                    ib.tapped();
                }
            }
        }
        Tip { visible: ibm.containsMouse; text: ib.tip }
    }

    // transport-control glyph button for the media popup
    component MediaBtn: Item {
        id: mb
        property string glyph: ""
        property bool active: true     // whether the action can be performed
        property bool on: false        // toggled-on state (shuffle/loop active)
        property bool accent: false    // primary-tinted (the play/pause button)
        property bool big: false
        signal tapped()
        implicitWidth: big ? 46 : 34
        implicitHeight: big ? 46 : 34
        Rectangle {
            anchors.centerIn: parent
            width: mb.big ? 44 : 32; height: width; radius: width / 2
            color: mb.accent ? Qt.rgba(root.cPrimary.r, root.cPrimary.g, root.cPrimary.b, 0.15) : "transparent"
            visible: mb.accent || mbm.containsMouse
            opacity: mbm.containsMouse ? 1.0 : 0.7
        }
        Text {
            anchors.centerIn: parent
            text: mb.glyph
            color: (mb.accent || mb.on) ? root.cPrimary : root.cOnSurface
            opacity: mb.active ? (mb.on || mb.accent ? 1.0 : 0.8) : 0.25
            font.family: root.uiFont
            font.pixelSize: mb.big ? 26 : 19
        }
        MouseArea {
            id: mbm
            anchors.fill: parent
            hoverEnabled: true
            enabled: mb.active
            cursorShape: Qt.PointingHandCursor
            onClicked: mb.tapped()
        }
    }

    // Selectable pill — mode + palette choices in the theme popup.
    component ThemeChip: Rectangle {
        id: chip
        property string glyph: ""
        property string label: ""
        property bool selected: false
        property bool enabled: true
        signal tapped()
        implicitHeight: 36
        implicitWidth: chipRow.implicitWidth + 26
        radius: 10
        color: chip.selected ? root.cPrimary
             : chipMa.containsMouse ? Qt.rgba(root.cPrimary.r, root.cPrimary.g, root.cPrimary.b, 0.16)
             : root.cSurfaceHigh
        border.width: chip.selected ? 0 : 1
        border.color: Qt.rgba(root.cOutline.r, root.cOutline.g, root.cOutline.b, 0.45)
        opacity: chip.enabled ? 1.0 : 0.4
        scale: chipMa.pressed ? 0.96 : 1.0
        Behavior on color { ColorAnimation { duration: 130 } }
        Behavior on scale { NumberAnimation { duration: 90 } }
        RowLayout {
            id: chipRow
            anchors.centerIn: parent
            spacing: 7
            Text {
                visible: chip.glyph !== ""
                text: chip.glyph
                color: chip.selected ? root.cOnPrimary : root.cPrimary
                font.family: root.uiFont; font.pixelSize: 15
            }
            Text {
                text: chip.label
                color: chip.selected ? root.cOnPrimary : root.cOnSurface
                font.family: root.uiFont; font.pixelSize: 13; font.bold: chip.selected
            }
        }
        MouseArea {
            id: chipMa
            anchors.fill: parent
            hoverEnabled: true
            enabled: chip.enabled
            cursorShape: Qt.PointingHandCursor
            onClicked: chip.tapped()
        }
    }

    // Custom slider — opacity + contrast in the theme popup. Commits on release.
    component ThemeSlider: Item {
        id: sl
        property string label: ""
        property real value: 0            // 0..1, shown when not dragging
        property color accent: root.cPrimary
        signal committed(real frac)
        property real dragFrac: -1
        readonly property real frac: sl.dragFrac >= 0 ? sl.dragFrac : sl.value
        implicitHeight: 46
        ColumnLayout {
            anchors.fill: parent
            spacing: 7
            RowLayout {
                Layout.fillWidth: true
                Text { text: sl.label; color: root.cOnSurface; opacity: 0.85; font.family: root.uiFont; font.pixelSize: 12 }
                Item { Layout.fillWidth: true }
                Text {
                    text: Math.round(sl.frac * 100) + "%"
                    color: sl.accent; font.family: root.uiFont; font.pixelSize: 12; font.bold: true
                }
            }
            Item {
                id: track
                Layout.fillWidth: true
                implicitHeight: 18
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width; height: 6; radius: 3
                    color: root.cSurfaceHigh
                }
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    width: Math.max(6, parent.width * sl.frac); height: 6; radius: 3
                    color: sl.accent
                    Behavior on width { enabled: sl.dragFrac < 0; NumberAnimation { duration: 110 } }
                }
                Rectangle {
                    width: 16; height: 16; radius: 8
                    color: sl.accent
                    border.width: 3; border.color: root.cBg
                    y: (parent.height - height) / 2
                    x: Math.max(0, Math.min(parent.width - width, parent.width * sl.frac - width / 2))
                    scale: trackMa.pressed ? 1.18 : 1.0
                    Behavior on scale { NumberAnimation { duration: 90 } }
                }
                MouseArea {
                    id: trackMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    function setFrac(mx) { sl.dragFrac = Math.max(0, Math.min(1, mx / track.width)); }
                    onPressed: (m) => setFrac(m.x)
                    onPositionChanged: (m) => { if (pressed) setFrac(m.x); }
                    onReleased: {
                        if (sl.dragFrac >= 0) { sl.committed(sl.dragFrac); sl.dragFrac = -1; }
                    }
                }
            }
        }
    }

    // Calendar + power popups: single instances shared by every monitor's bar.
    CalendarWindow {
        id: calendarWin
        cPrimary: root.cPrimary
        cOnPrimary: root.cOnPrimary
        cBg: root.cBg
        cOnSurface: root.cOnSurface
        uiFont: root.uiFont
    }
    PowerWindow {
        id: powerWin
        cPrimary: root.cPrimary
        cOnPrimary: root.cOnPrimary
        cBg: root.cBg
        uiFont: root.uiFont
    }

    // One bar per monitor
    Variants {
        model: Quickshell.screens

        PanelWindow {
            id: bar
            required property var modelData
            screen: modelData

            WlrLayershell.namespace: "quickshell:bar-mh"
            WlrLayershell.layer: WlrLayer.Top
            color: "transparent"

            anchors { top: true; left: true; right: true }
            implicitHeight: root.barHeight + root.topGap + root.popupRoom
            exclusiveZone: root.barHeight + root.topGap
            mask: Region { item: barBg }

            Rectangle {
                id: barBg
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.topMargin: root.topGap
                anchors.leftMargin: root.sideMargin
                anchors.rightMargin: root.sideMargin
                height: root.barHeight
                radius: 12
                // Static gradient border matching the Hyprland window border:
                // dark sides (on_primary) -> bright centre (primary) -> dark sides.
                // No rotation here (that's Hyprland-only).
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0;  color: root.cOnPrimary }
                    GradientStop { position: 0.18; color: root.cOnPrimary }
                    GradientStop { position: 0.35; color: root.cPrimary }
                    GradientStop { position: 0.65; color: root.cPrimary }
                    GradientStop { position: 0.82; color: root.cOnPrimary }
                    GradientStop { position: 1.0;  color: root.cOnPrimary }
                }

                // Inner background, inset by the border width so the gradient above
                // shows only as a border ring. Honors theme opacity (0–100) via
                // colour alpha (not Item.opacity) so text/icons stay crisp.
                Rectangle {
                    id: barInner
                    anchors.fill: parent
                    anchors.margins: root.barBorderWidth
                    radius: parent.radius - root.barBorderWidth
                    color: Qt.rgba(root.cBg.r, root.cBg.g, root.cBg.b, root.thOpacity / 100)
                }

                RowLayout {
                    anchors.fill: barInner
                    anchors.leftMargin: 12
                    anchors.rightMargin: 14
                    spacing: 10

                    // workspaces
                    Row {
                        Layout.alignment: Qt.AlignVCenter
                        spacing: 6
                        Repeater {
                            model: 9                                    // always show workspaces 1–9
                            delegate: Rectangle {
                                id: wsPill
                                required property int index
                                readonly property int wsId: index + 1
                                readonly property bool isActive:
                                    wsId === (Hyprland.focusedMonitor?.activeWorkspace?.id ?? -1)
                                readonly property bool occupied: (root.wsWindows["" + wsId] || []).length > 0
                                width: 30
                                height: 26
                                radius: 6
                                color: wsPill.isActive ? root.cPrimary : "transparent"
                                Text {
                                    anchors.centerIn: parent
                                    text: wsPill.wsId
                                    color: wsPill.isActive ? root.cBg : root.cPrimary
                                    opacity: wsPill.isActive || wsPill.occupied ? 1.0 : 0.3   // dim empty workspaces
                                    font.family: root.numFont
                                    font.pixelSize: 16
                                }
                                MouseArea {
                                    id: wsHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (Hyprland.usingLua)
                                            Hyprland.dispatch("hl.dsp.focus({workspace = '" + wsPill.wsId + "'})");
                                        else
                                            Hyprland.dispatch("workspace " + wsPill.wsId);
                                    }
                                    onWheel: (wheel) => root.switchWorkspaceRel(wheel.angleDelta.y > 0 ? -1 : 1)
                                }
                                WsTip { visible: wsHover.containsMouse; wsId: wsPill.wsId }
                            }
                        }
                    }

                    Sep {}

                    Text {   // focused app
                        id: appText
                        Layout.alignment: Qt.AlignVCenter
                        Layout.maximumWidth: 280
                        elide: Text.ElideRight
                        text: root.focusedApp
                        color: root.cPrimary
                        font.family: root.uiFont
                        font.pixelSize: 16
                        font.bold: true
                        MouseArea {
                            id: appHover
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: root.focusedPid > 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: {
                                if (root.focusedPid > 0)
                                    Quickshell.execDetached(["ghostty", "-e", "htop", "-p", "" + root.focusedPid]);
                            }
                        }
                        AppTip { visible: appHover.containsMouse && root.focusedApp !== "" }
                    }

                    Sep {}

                    Text {   // big clock — click opens the ML4W calendar
                        id: clock
                        Layout.alignment: Qt.AlignVCenter
                        color: root.cPrimary
                        font.family: root.numFont
                        font.pixelSize: 26
                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: calendarWin.toggleAt(root.popupLeft(clock, bar.width, 380))
                        }
                        Timer {
                            interval: 1000; running: true; repeat: true; triggeredOnStart: true
                            onTriggered: clock.text = Qt.formatDateTime(new Date(), "HH:mm")
                        }
                    }

                    // flexible spacer
                    Item { Layout.fillWidth: true }

                    // date — digits in ttyclock (align with clock), "/" rendered separately
                    Item {
                        id: dateBox
                        property string tipText: ""
                        Layout.alignment: Qt.AlignVCenter
                        implicitWidth: dateRow.implicitWidth
                        implicitHeight: dateRow.implicitHeight
                        Row {
                            id: dateRow
                            anchors.centerIn: parent
                            spacing: 2
                            Text { id: dDay; anchors.verticalCenter: parent.verticalCenter
                                   color: root.cPrimary; font.family: root.numFont; font.pixelSize: 26 }
                            Text { anchors.verticalCenter: parent.verticalCenter; text: "/"
                                   color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 20 }
                            Text { id: dMon; anchors.verticalCenter: parent.verticalCenter
                                   color: root.cPrimary; font.family: root.numFont; font.pixelSize: 26 }
                        }
                        MouseArea {
                            id: dateHover
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: calendarWin.toggleAt(root.popupLeft(dateBox, bar.width, 380))
                        }
                        Tip { visible: dateHover.containsMouse; text: dateBox.tipText }
                        Timer {
                            interval: 30000; running: true; repeat: true; triggeredOnStart: true
                            onTriggered: {
                                const d = new Date();
                                dDay.text = Qt.formatDateTime(d, "dd");
                                dMon.text = Qt.formatDateTime(d, "MM");
                                dateBox.tipText = Qt.formatDateTime(d, "dddd, dd MMMM yyyy");
                            }
                        }
                    }

                    Sep {}

                    Stat { icon: "󰻠"; raw: root.cpuRaw;  label: "CPU usage";   popupTarget: "proc" }
                    Stat { icon: "󰍛"; raw: root.memRaw;  label: "Memory used"; popupTarget: "proc" }
                    Stat { icon: "󰋊"; raw: root.diskRaw; label: "Disk free (/)" }
                    Stat {   // scroll: volume ±5% (capped 100%) · left: pavucontrol · right: mute
                        icon: value === "" ? "󰖁" : "󰕾"   // 󰖁 when muted
                        raw: root.volRaw
                        clickCmd: "pavucontrol"
                        rightCmd: "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"
                        scrollUpCmd: "wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+"
                        scrollDownCmd: "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"
                        onActed: volRefreshSoon.restart()
                    }
                    Stat { icon: "󰖩"; raw: root.netRaw;  clickCmd: root.scriptDir + "network.sh" }

                    // system tray — app icons recolored to the bar accent via ColorOverlay
                    Row {
                        Layout.alignment: Qt.AlignVCenter
                        spacing: 8
                        visible: SystemTray.items.values.length > 0
                        Repeater {
                            model: SystemTray.items
                            delegate: MouseArea {
                                id: trayDelegate
                                required property var modelData
                                implicitWidth: 20
                                implicitHeight: 20
                                hoverEnabled: true
                                acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
                                cursorShape: Qt.PointingHandCursor
                                onClicked: (mouse) => {
                                    if (mouse.button === Qt.MiddleButton) {
                                        modelData.secondaryActivate();
                                    } else if (mouse.button === Qt.RightButton || modelData.onlyMenu) {
                                        if (modelData.hasMenu) {
                                            // compute fresh position at click time (a binding evaluates too early → x=0)
                                            const p = trayDelegate.mapToItem(null, 0, 0);
                                            trayMenu.anchor.rect = Qt.rect(p.x, root.barHeight + root.topGap + 4, trayDelegate.width, 1);
                                            trayMenu.open();   // context menu (right-click, or left-click for menu-only items)
                                        }
                                    } else {
                                        modelData.activate();
                                    }
                                }
                                IconImage {
                                    anchors.centerIn: parent
                                    width: 16; height: 16
                                    source: modelData.icon
                                    // Skip the accent tint for full-color icons (root.trayNoTint): ColorOverlay
                                    // masks by alpha, so an opaque bitmap would flatten into a solid square.
                                    readonly property bool tintable: {
                                        const k = ((modelData.id || "") + " " + (modelData.title || "")
                                                   + " " + (modelData.tooltipTitle || "")).toLowerCase();
                                        return !root.trayNoTint.some(s => k.indexOf(s) >= 0);
                                    }
                                    layer.enabled: tintable
                                    layer.effect: ColorOverlay { color: root.cPrimary }  // accent tint (monochrome icons only)
                                }
                                Tip { visible: trayDelegate.containsMouse; text: modelData.tooltipTitle || modelData.title || modelData.id }
                                QsMenuAnchor {
                                    id: trayMenu
                                    menu: modelData.menu
                                    anchor.window: bar
                                    // anchor.rect is set imperatively in onClicked (see above)
                                }
                            }
                        }
                    }

                    Sep {}

                    // pending updates — hidden when none; left: update all · right: list
                    MouseArea {
                        id: updWidget
                        Layout.alignment: Qt.AlignVCenter
                        visible: root.updateCount > 0
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        implicitWidth: updRow.implicitWidth
                        implicitHeight: updRow.implicitHeight
                        onClicked: (mouse) => {
                            if (mouse.button === Qt.RightButton) {
                                root.updListX = updWidget.mapToItem(null, updWidget.width / 2, 0).x;
                                root.updListScreen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
                                root.updListOpen = !root.updListOpen;   // Connections fetches + sets loading
                            } else {
                                Quickshell.execDetached(["ghostty", "-e", "bash", root.scriptDir + "run-updates.sh"]);
                            }
                        }
                        RowLayout {
                            id: updRow
                            anchors.centerIn: parent
                            spacing: 5
                            Text { Layout.alignment: Qt.AlignVCenter; text: "\uf1b2"; color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 15 }
                            Text { Layout.alignment: Qt.AlignVCenter; text: root.updateCount; color: root.cPrimary; font.family: root.numFont; font.pixelSize: 15 }
                        }
                        Tip {
                            visible: updWidget.containsMouse
                            text: root.updateCount + " update" + (root.updateCount === 1 ? "" : "s")
                                  + (root.updateTip !== "" ? "  (" + root.updateTip + ")" : "")
                                  + "\nLeft: update all   ·   Right: list"
                        }
                    }

                    // theme control — click opens the theme menu (SketchyBar parity)
                    MouseArea {
                        id: themeWidget
                        Layout.alignment: Qt.AlignVCenter
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        implicitWidth: themeRow.implicitWidth
                        implicitHeight: themeRow.implicitHeight
                        onClicked: {
                            if (root.themeOpen) { root.themeOpen = false; return; }
                            root.openThemeAt(themeWidget.mapToItem(null, themeWidget.width / 2, 0).x);
                        }
                        RowLayout {
                            id: themeRow
                            anchors.centerIn: parent
                            spacing: 5
                            Text {
                                Layout.alignment: Qt.AlignVCenter
                                text: "󰏘"
                                color: root.cPrimary
                                opacity: root.themeOpen || themeWidget.containsMouse ? 1.0 : 0.92
                                font.family: root.uiFont; font.pixelSize: 17
                            }
                            Text {
                                Layout.alignment: Qt.AlignVCenter
                                text: root.thPretty
                                color: root.cPrimary
                                font.family: root.uiFont; font.pixelSize: 14; font.bold: true
                            }
                        }
                        Tip {
                            visible: themeWidget.containsMouse
                            text: "Theme: " + root.thPretty + " · " + root.thVariant + " · " + root.thOpacity + "%"
                                  + "\nClick to customize"
                        }
                    }

                    IconButton {
                        // 󰂛 off (DND) · 󰂞 ring/unseen (solid) · 󰂚 bell (idle)
                        text: root.notifDnd ? "󰂛" : (root.notifHas ? "󰂞" : "󰂚")
                        tip: (root.notifCount > 0 ? root.notifCount + " notification" + (root.notifCount === 1 ? "" : "s") + "\n" : "")
                             + (root.notifDnd ? "Do-not-disturb is ON\n" : "")
                             + "Left: notifications   ·   Right: do-not-disturb"
                        cmd: "swaync-client -t -sw"
                        cmdRight: "swaync-client -d -sw"
                    }
                    IconButton { text: "󰐥"; tip: "Power menu"; onTapped: powerWin.toggle() }
                }

                // Centered now-playing (MPRIS) — floats over the bar's flexible middle.
                // Hidden when nothing is playable. Left: controls popup · Middle: play/pause · Wheel: prev/next.
                MouseArea {
                    id: mediaWidget
                    visible: root.player !== null
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: visible ? mediaRow.implicitWidth : 0
                    height: mediaRow.implicitHeight
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    opacity: (root.player && root.player.isPlaying) ? 1.0 : 0.6
                    onClicked: (mouse) => {
                        if (mouse.button === Qt.RightButton) {
                            if (root.player) root.player.togglePlaying();
                            return;
                        }
                        if (root.mediaOpen) { root.mediaOpen = false; return; }
                        root.mediaX = mediaWidget.mapToItem(null, mediaWidget.width / 2, 0).x;
                        root.mediaScreen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
                        root.mediaOpen = true;
                    }
                    onWheel: (wheel) => {
                        if (!root.player) return;
                        if (wheel.angleDelta.y > 0) root.player.next();
                        else if (wheel.angleDelta.y < 0) root.player.previous();
                    }
                    RowLayout {
                        id: mediaRow
                        anchors.centerIn: parent
                        spacing: 7
                        Text {
                            Layout.alignment: Qt.AlignVCenter
                            text: "󰐊"
                            color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 14
                        }
                        Text {
                            Layout.alignment: Qt.AlignVCenter
                            Layout.maximumWidth: 240
                            text: root.player ? (root.player.trackTitle || root.player.identity || "Media") : ""
                            color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 15; font.bold: true
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.alignment: Qt.AlignVCenter
                            Layout.maximumWidth: 160
                            visible: root.player && root.player.trackArtist !== ""
                            text: root.player && root.player.trackArtist ? "· " + root.player.trackArtist : ""
                            color: root.cOnSurface; opacity: 0.6; font.family: root.uiFont; font.pixelSize: 13
                            elide: Text.ElideRight
                        }
                    }
                    Tip {
                        visible: mediaWidget.containsMouse
                        text: (root.player ? (root.player.trackTitle || root.player.identity || "Media") : "")
                              + (root.player && root.player.trackArtist ? "\n" + root.player.trackArtist : "")
                              + "\nLeft: controls   ·   Right: play/pause   ·   Scroll: prev/next"
                    }
                }
            }

            // ---- Process monitor popup (CPU/RAM click) ----
            PanelWindow {
                id: procPopup
                screen: bar.screen
                WlrLayershell.layer: WlrLayer.Overlay
                WlrLayershell.namespace: "quickshell:procmon"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand  // Escape works, and (unlike Exclusive) click-away still dismisses
                exclusionMode: WlrLayershell.Ignore
                color: "transparent"
                anchors { top: true; left: true }
                implicitWidth: 420
                implicitHeight: 400

                // Latched to the screen the popup opened on (root.procScreen) so it stays
                // put even if monitor focus changes while open. Only this screen shows the
                // popup and arms a focus grab (Hyprland allows only ONE grab).
                readonly property bool onActiveScreen: bar.screen.name === root.procScreen
                // Mapped while open OR mid slide-out animation — no manual showWindow flag.
                visible: (root.procOpen || procSlide.running) && onActiveScreen

                Connections {
                    target: root
                    function onProcOpenChanged() {
                        if (root.procOpen) {
                            procRefresh.running = true;
                            if (procPopup.onActiveScreen)
                                procGrabArm.restart();  // arm focus grab (only on the screen it opened on)
                        } else {
                            procGrab.active = false;
                            procGrabArm.stop();
                        }
                    }
                }

                property real currentTopMargin: root.procOpen ? root.barHeight + root.topGap + 6 : -420
                margins {
                    top: procPopup.currentTopMargin
                    // center under the CPU/RAM stat that opened it, clamped on-screen
                    left: Math.max(0, Math.min(Math.round(root.procClickX - procPopup.implicitWidth / 2),
                                               bar.width - procPopup.implicitWidth))
                }

                Behavior on currentTopMargin {
                    NumberAnimation {
                        id: procSlide
                        duration: 350
                        easing.type: Easing.OutQuint
                    }
                }

                // Click-outside-to-close. The bar is included so clicking the CPU/RAM
                // stats (to toggle/switch) doesn't dismiss; only truly-outside clicks do.
                // Armed a beat AFTER opening (via procGrabArm) so the opening click
                // itself doesn't immediately clear the grab.
                HyprlandFocusGrab {
                    id: procGrab
                    windows: [procPopup, bar]
                    active: false
                    onCleared: { if (root.procOpen) root.procOpen = false }
                }
                Timer { id: procGrabArm; interval: 150; onTriggered: procGrab.active = true }

                // Live refresh while open.
                Timer {
                    interval: 3000
                    running: root.procOpen
                    repeat: true
                    onTriggered: procRefresh.running = true
                }

                Item {
                    anchors.fill: parent
                    anchors.margins: 20
                    focus: true
                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Escape) { root.procOpen = false; event.accepted = true; }
                    }

                    GradientBorder {
                        id: procBg
                        anchors.fill: parent
                        darkColor: root.cOnPrimary
                        brightColor: root.cPrimary
                        fillColor: root.cBg
                        borderWidth: 2
                        radius: 10
                        opacity: 0.95
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 10

                        // header
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 24
                            RowLayout {
                                anchors.fill: parent
                                Text {
                                    text: (root.procFilter === "cpu" ? "󰻠" : "󰍛") + "  Processes"
                                    color: root.cPrimary
                                    font.family: root.uiFont
                                    font.pixelSize: 14
                                    font.bold: true
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: "by CPU"
                                    color: root.procFilter === "cpu" ? root.cPrimary : root.cOnSurface
                                    opacity: root.procFilter === "cpu" ? 1.0 : 0.4
                                    font.family: root.uiFont
                                    font.pixelSize: 12
                                    MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: { root.procFilter = "cpu"; procRefresh.running = true } }
                                }
                                Text { text: " │ "; color: root.cOutline; font.family: root.uiFont; font.pixelSize: 12 }
                                Text {
                                    text: "by MEM"
                                    color: root.procFilter === "mem" ? root.cPrimary : root.cOnSurface
                                    opacity: root.procFilter === "mem" ? 1.0 : 0.4
                                    font.family: root.uiFont
                                    font.pixelSize: 12
                                    MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: { root.procFilter = "mem"; procRefresh.running = true } }
                                }
                                Text { text: "  "; font.pixelSize: 12 }
                                Text {
                                    text: "↻"
                                    color: root.cPrimary
                                    font.family: root.uiFont
                                    font.pixelSize: 14
                                    MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: procRefresh.running = true }
                                }
                            }
                        }

                        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.cPrimary; opacity: 0.3 }

                        // column headers
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text { Layout.preferredWidth: 50; text: "PID"; color: root.cOnSurface; opacity: 0.5; font.family: root.uiFont; font.pixelSize: 12; font.bold: true }
                            Text { Layout.preferredWidth: 55; text: "CPU%"; color: root.cOnSurface; opacity: 0.5; font.family: root.uiFont; font.pixelSize: 12; font.bold: true; horizontalAlignment: Text.AlignRight }
                            Text { Layout.preferredWidth: 55; text: "MEM%"; color: root.cOnSurface; opacity: 0.5; font.family: root.uiFont; font.pixelSize: 12; font.bold: true; horizontalAlignment: Text.AlignRight }
                            Text { Layout.fillWidth: true; text: "COMMAND"; color: root.cOnSurface; opacity: 0.5; font.family: root.uiFont; font.pixelSize: 12; font.bold: true }
                        }

                        // process list
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: procModel
                            clip: true
                            spacing: 2

                            delegate: Rectangle {
                                required property var model
                                width: ListView.view.width
                                height: 24
                                radius: 4
                                color: procHover.containsMouse ? Qt.rgba(root.cPrimary.r, root.cPrimary.g, root.cPrimary.b, 0.08) : "transparent"

                                MouseArea {
                                    id: procHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 4
                                    anchors.rightMargin: 4
                                    spacing: 8
                                    Text { Layout.preferredWidth: 50; text: model.pid; color: root.cOnSurface; opacity: 0.6; font.family: root.uiFont; font.pixelSize: 12 }
                                    Text { Layout.preferredWidth: 55; text: model.cpu.toFixed(1); color: model.cpu > 50 ? root.cError : root.cPrimary; font.family: root.uiFont; font.pixelSize: 12; horizontalAlignment: Text.AlignRight }
                                    Text { Layout.preferredWidth: 55; text: model.mem.toFixed(1); color: model.mem > 50 ? root.cError : root.cPrimary; font.family: root.uiFont; font.pixelSize: 12; horizontalAlignment: Text.AlignRight }
                                    Text { Layout.fillWidth: true; text: model.cmd; color: root.cOnSurface; font.family: root.uiFont; font.pixelSize: 12; elide: Text.ElideRight }
                                }
                            }
                        }
                    }
                }
            }

            // ---- Updates list popup (right-click the updates badge) ----
            PanelWindow {
                id: updPopup
                screen: bar.screen
                WlrLayershell.layer: WlrLayer.Overlay
                WlrLayershell.namespace: "quickshell:updates"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
                exclusionMode: WlrLayershell.Ignore
                color: "transparent"
                anchors { top: true; left: true }
                implicitWidth: 380
                implicitHeight: 440

                readonly property bool onActiveScreen: bar.screen.name === root.updListScreen
                visible: (root.updListOpen || updSlide.running) && onActiveScreen

                Connections {
                    target: root
                    function onUpdListOpenChanged() {
                        if (root.updListOpen) {
                            root.updLoading = true;
                            updListProc.running = true;
                            if (updPopup.onActiveScreen) updGrabArm.restart();
                        } else {
                            updGrab.active = false;
                            updGrabArm.stop();
                        }
                    }
                }

                property real currentTopMargin: root.updListOpen ? root.barHeight + root.topGap + 6 : -460
                margins {
                    top: updPopup.currentTopMargin
                    left: Math.max(0, Math.min(Math.round(root.updListX - updPopup.implicitWidth / 2),
                                               bar.width - updPopup.implicitWidth))
                }

                Behavior on currentTopMargin {
                    NumberAnimation { id: updSlide; duration: 350; easing.type: Easing.OutQuint }
                }

                HyprlandFocusGrab {
                    id: updGrab
                    windows: [updPopup, bar]
                    active: false
                    onCleared: { if (root.updListOpen) root.updListOpen = false }
                }
                Timer { id: updGrabArm; interval: 150; onTriggered: updGrab.active = true }

                Item {
                    anchors.fill: parent
                    anchors.margins: 20
                    focus: true
                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Escape) { root.updListOpen = false; event.accepted = true; }
                    }

                    GradientBorder {
                        anchors.fill: parent
                        darkColor: root.cOnPrimary
                        brightColor: root.cPrimary
                        fillColor: root.cBg
                        borderWidth: 2
                        radius: 10
                        opacity: 0.95
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "\uf1b2  Updates"; color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 14; font.bold: true }
                            Item { Layout.fillWidth: true }
                            Text { text: root.updLoading ? "checking…" : root.updateCount + " pending"; color: root.cOnSurface; opacity: 0.6; font.family: root.uiFont; font.pixelSize: 12 }
                        }
                        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.cPrimary; opacity: 0.3 }

                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: updModel
                            clip: true
                            spacing: 2
                            delegate: Rectangle {
                                required property var model
                                width: ListView.view.width
                                height: 34
                                radius: 4
                                color: updHover.containsMouse ? Qt.rgba(root.cPrimary.r, root.cPrimary.g, root.cPrimary.b, 0.10) : "transparent"
                                MouseArea {
                                    id: updHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        Quickshell.execDetached(["ghostty", "-e", "bash", root.scriptDir + "update-one.sh", model.name, model.src]);
                                        root.updListOpen = false;
                                    }
                                }
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 6
                                    anchors.rightMargin: 6
                                    anchors.topMargin: 4
                                    anchors.bottomMargin: 4
                                    spacing: 1
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        Text { Layout.fillWidth: true; text: model.name; color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                                        Text { text: model.src; color: root.cOnSurface; opacity: 0.4; font.family: root.uiFont; font.pixelSize: 10 }
                                    }
                                    Text { Layout.fillWidth: true; text: model.oldv + "  →  " + model.newv; color: root.cOnSurface; opacity: 0.55; font.family: root.uiFont; font.pixelSize: 10; elide: Text.ElideRight }
                                }
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "Click a package to update it on its own"
                            color: root.cOnSurface; opacity: 0.4; font.family: root.uiFont; font.pixelSize: 10; font.italic: true
                        }
                    }
                }
            }

            // ---- Media controls popup (click the centered now-playing) ----
            PanelWindow {
                id: mediaPopup
                screen: bar.screen
                WlrLayershell.layer: WlrLayer.Overlay
                WlrLayershell.namespace: "quickshell:media"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
                exclusionMode: WlrLayershell.Ignore
                color: "transparent"
                anchors { top: true; left: true }
                implicitWidth: 400
                implicitHeight: 260

                readonly property bool onActiveScreen: bar.screen.name === root.mediaScreen
                visible: (root.mediaOpen || mediaSlide.running) && onActiveScreen && root.player !== null

                Connections {
                    target: root
                    function onMediaOpenChanged() {
                        if (root.mediaOpen) {
                            root.mediaPos = root.player ? root.player.position : 0;
                            if (mediaPopup.onActiveScreen) mediaGrabArm.restart();
                        } else {
                            mediaGrab.active = false;
                            mediaGrabArm.stop();
                        }
                    }
                }

                property real currentTopMargin: root.mediaOpen ? root.barHeight + root.topGap + 6 : -280
                margins {
                    top: mediaPopup.currentTopMargin
                    left: Math.max(0, Math.min(Math.round(root.mediaX - mediaPopup.implicitWidth / 2),
                                               bar.width - mediaPopup.implicitWidth))
                }

                Behavior on currentTopMargin {
                    NumberAnimation { id: mediaSlide; duration: 350; easing.type: Easing.OutQuint }
                }

                HyprlandFocusGrab {
                    id: mediaGrab
                    windows: [mediaPopup, bar]
                    active: false
                    onCleared: { if (root.mediaOpen) root.mediaOpen = false }
                }
                Timer { id: mediaGrabArm; interval: 150; onTriggered: mediaGrab.active = true }

                Item {
                    anchors.fill: parent
                    anchors.margins: 20
                    focus: true
                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Escape) { root.mediaOpen = false; event.accepted = true; }
                    }

                    GradientBorder {
                        anchors.fill: parent
                        darkColor: root.cOnPrimary
                        brightColor: root.cPrimary
                        fillColor: root.cBg
                        borderWidth: 2
                        radius: 10
                        opacity: 0.95
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12

                        // ---- album art + track info ----
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14

                            ClippingRectangle {
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 78; implicitHeight: 78
                                radius: 10
                                color: Qt.rgba(root.cPrimary.r, root.cPrimary.g, root.cPrimary.b, 0.12)
                                Image {
                                    id: artImg
                                    anchors.fill: parent
                                    source: root.player && root.player.trackArtUrl ? root.player.trackArtUrl : ""
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    cache: true
                                    visible: status === Image.Ready
                                }
                                Text {
                                    anchors.centerIn: parent
                                    visible: artImg.status !== Image.Ready
                                    text: "♫"; color: root.cPrimary; opacity: 0.5
                                    font.family: root.uiFont; font.pixelSize: 34
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: { if (root.player && root.player.canRaise) root.player.raise() }
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 3

                                // player identity + switcher (only when >1 player)
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    Text {
                                        Layout.fillWidth: true
                                        text: root.player ? (root.player.identity || "Unknown player") : ""
                                        color: root.cOnSurface; opacity: 0.55
                                        font.family: root.uiFont; font.pixelSize: 11
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        visible: root.mediaPlayers.length > 1
                                        text: "switch ⇄"
                                        color: root.cPrimary; opacity: switchMa.containsMouse ? 1.0 : 0.6
                                        font.family: root.uiFont; font.pixelSize: 11
                                        MouseArea {
                                            id: switchMa
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: root.cyclePlayer()
                                        }
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: root.player ? (root.player.trackTitle || "—") : ""
                                    color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 15; font.bold: true
                                    elide: Text.ElideRight
                                    maximumLineCount: 2; wrapMode: Text.Wrap
                                }
                                Text {
                                    Layout.fillWidth: true
                                    visible: root.player && root.player.trackArtist !== ""
                                    text: root.player ? root.player.trackArtist : ""
                                    color: root.cOnSurface; font.family: root.uiFont; font.pixelSize: 13
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    visible: root.player && root.player.trackAlbum !== ""
                                    text: root.player ? root.player.trackAlbum : ""
                                    color: root.cOnSurface; opacity: 0.5; font.family: root.uiFont; font.pixelSize: 11; font.italic: true
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        // ---- progress / seek ----
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            visible: root.player && root.player.lengthSupported && root.player.length > 0

                            Item {
                                id: seekBar
                                Layout.fillWidth: true
                                implicitHeight: 12
                                readonly property real frac: (root.player && root.player.length > 0)
                                    ? Math.max(0, Math.min(1, root.mediaPos / root.player.length)) : 0
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width; height: 4; radius: 2
                                    color: root.cOutline; opacity: 0.4
                                }
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width * seekBar.frac; height: 4; radius: 2
                                    color: root.cPrimary
                                }
                                Rectangle {
                                    width: 11; height: 11; radius: 5.5
                                    color: root.cPrimary
                                    y: (parent.height - height) / 2
                                    x: Math.max(0, Math.min(parent.width - width, parent.width * seekBar.frac - width / 2))
                                    visible: root.player && root.player.canSeek
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    enabled: root.player && root.player.canSeek
                                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: (m) => {
                                        if (root.player && root.player.length > 0) {
                                            root.player.position = (m.x / width) * root.player.length;
                                            root.mediaPos = root.player.position;
                                        }
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: root.fmtTime(root.mediaPos); color: root.cOnSurface; opacity: 0.6; font.family: root.uiFont; font.pixelSize: 10 }
                                Item { Layout.fillWidth: true }
                                Text { text: root.fmtTime(root.player ? root.player.length : 0); color: root.cOnSurface; opacity: 0.6; font.family: root.uiFont; font.pixelSize: 10 }
                            }
                        }

                        // ---- transport controls ----
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Item { Layout.fillWidth: true }
                            MediaBtn {
                                glyph: "󰒟"
                                active: root.player && root.player.shuffleSupported
                                on: root.player && root.player.shuffle
                                onTapped: { if (root.player) root.player.shuffle = !root.player.shuffle }
                            }
                            MediaBtn {
                                glyph: "󰒮"
                                active: root.player && root.player.canGoPrevious
                                onTapped: { if (root.player) root.player.previous() }
                            }
                            MediaBtn {
                                glyph: root.player && root.player.isPlaying ? "󰏤" : "󰐊"
                                accent: true; big: true
                                active: root.player && root.player.canTogglePlaying
                                onTapped: { if (root.player) root.player.togglePlaying() }
                            }
                            MediaBtn {
                                glyph: "󰒭"
                                active: root.player && root.player.canGoNext
                                onTapped: { if (root.player) root.player.next() }
                            }
                            MediaBtn {
                                glyph: root.player && root.player.loopState === MprisLoopState.Track ? "󰑘" : "󰑖"
                                active: root.player && root.player.loopSupported
                                on: root.player && root.player.loopState !== MprisLoopState.None
                                onTapped: root.cycleLoop()
                            }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }
            }

            // ---- Theme control popup (palette / mode / opacity / contrast) ----
            PanelWindow {
                id: themePopup
                screen: bar.screen
                WlrLayershell.layer: WlrLayer.Overlay
                WlrLayershell.namespace: "quickshell:theme"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
                exclusionMode: WlrLayershell.Ignore
                color: "transparent"
                anchors { top: true; left: true }
                implicitWidth: 360
                implicitHeight: themeCol.implicitHeight + 72   // 20 outer + 16 inner, both sides

                readonly property bool onActiveScreen: bar.screen.name === root.themeScreen
                visible: (root.themeOpen || themeSlide.running) && onActiveScreen

                Connections {
                    target: root
                    function onThemeOpenChanged() {
                        if (root.themeOpen) {
                            themeStateProc.running = true;
                            if (themePopup.onActiveScreen) themeGrabArm.restart();
                        } else {
                            themeGrab.active = false;
                            themeGrabArm.stop();
                        }
                    }
                }

                property real currentTopMargin: root.themeOpen
                    ? root.barHeight + root.topGap + 6
                    : -(themePopup.implicitHeight + 20)
                margins {
                    top: themePopup.currentTopMargin
                    left: Math.max(0, Math.min(Math.round(root.themeX - themePopup.implicitWidth / 2),
                                               bar.width - themePopup.implicitWidth))
                }

                Behavior on currentTopMargin {
                    NumberAnimation { id: themeSlide; duration: 360; easing.type: Easing.OutQuint }
                }

                HyprlandFocusGrab {
                    id: themeGrab
                    windows: [themePopup, bar]
                    active: false
                    onCleared: { if (root.themeOpen) root.themeOpen = false }
                }
                Timer { id: themeGrabArm; interval: 150; onTriggered: themeGrab.active = true }

                Item {
                    anchors.fill: parent
                    anchors.margins: 20
                    focus: true
                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Escape) { root.themeOpen = false; event.accepted = true; }
                    }

                    GradientBorder {
                        anchors.fill: parent
                        darkColor: root.cOnPrimary
                        brightColor: root.cPrimary
                        fillColor: root.cBg
                        borderWidth: 2
                        radius: 14
                        opacity: 0.97
                    }

                    ColumnLayout {
                        id: themeCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 13

                        // ---- header ----
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 11
                            Rectangle {
                                implicitWidth: 38; implicitHeight: 38; radius: 12
                                color: root.cPrimaryContainer
                                Text {
                                    anchors.centerIn: parent
                                    text: "󰏘"; color: root.cPrimary
                                    font.family: root.uiFont; font.pixelSize: 20
                                }
                            }
                            ColumnLayout {
                                spacing: 1
                                Text {
                                    text: "Theme"; color: root.cOnSurface
                                    font.family: root.uiFont; font.pixelSize: 16; font.bold: true
                                }
                                Text {
                                    text: root.themeBusy
                                        ? "applying…"
                                        : root.thPretty + " · " + (root.thLight ? "Light" : "Dark") + " · " + root.thOpacity + "%"
                                    color: root.themeBusy ? root.cPrimary : root.cOnSurface
                                    opacity: root.themeBusy ? 1.0 : 0.55
                                    font.family: root.uiFont; font.pixelSize: 11
                                }
                            }
                            Item { Layout.fillWidth: true }   // pushes the close button flush-right
                            Rectangle {
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 26; implicitHeight: 26; radius: 13
                                color: closeMa.containsMouse
                                    ? Qt.rgba(root.cError.r, root.cError.g, root.cError.b, 0.18)
                                    : "transparent"
                                Behavior on color { ColorAnimation { duration: 120 } }
                                Text {
                                    anchors.centerIn: parent
                                    text: "✕"
                                    color: closeMa.containsMouse ? root.cError : root.cOnSurface
                                    opacity: closeMa.containsMouse ? 1.0 : 0.45
                                    font.family: root.uiFont; font.pixelSize: 13
                                }
                                MouseArea {
                                    id: closeMa
                                    anchors.fill: parent
                                    hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: root.themeOpen = false
                                }
                            }
                        }

                        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.cPrimary; opacity: 0.18 }

                        // ---- appearance (light / dark) ----
                        Text {
                            text: "APPEARANCE"; color: root.cOutline
                            font.family: root.uiFont; font.pixelSize: 10; font.bold: true; font.letterSpacing: 1.5
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            ThemeChip {
                                Layout.fillWidth: true
                                glyph: "󰖔"; label: "Dark"
                                selected: !root.thLight; enabled: !root.themeBusy
                                onTapped: root.setMode("dark")
                            }
                            ThemeChip {
                                Layout.fillWidth: true
                                glyph: "󰖨"; label: "Light"
                                selected: root.thLight; enabled: !root.themeBusy
                                onTapped: root.setMode("light")
                            }
                        }

                        // ---- palette ----
                        Text {
                            text: "PALETTE"; color: root.cOutline
                            font.family: root.uiFont; font.pixelSize: 10; font.bold: true; font.letterSpacing: 1.5
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 8
                            rowSpacing: 8
                            ThemeChip { Layout.fillWidth: true; label: "Mocha";     selected: root.thName === "mocha";     enabled: !root.themeBusy; onTapped: root.setVariant("mocha") }
                            ThemeChip { Layout.fillWidth: true; label: "Latte";     selected: root.thName === "latte";     enabled: !root.themeBusy; onTapped: root.setVariant("latte") }
                            ThemeChip { Layout.fillWidth: true; label: "Frappé";    selected: root.thName === "frappe";    enabled: !root.themeBusy; onTapped: root.setVariant("frappe") }
                            ThemeChip { Layout.fillWidth: true; label: "Macchiato"; selected: root.thName === "macchiato"; enabled: !root.themeBusy; onTapped: root.setVariant("macchiato") }
                            ThemeChip { Layout.fillWidth: true; glyph: "󰸉"; label: "Dynamic"; selected: root.thDynamic; enabled: !root.themeBusy; onTapped: root.setDynamic() }
                        }

                        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.cPrimary; opacity: 0.12 }

                        // ---- opacity ----
                        ThemeSlider {
                            Layout.fillWidth: true
                            label: "Opacity"
                            value: root.thOpacity / 100
                            onCommitted: (frac) => root.setOpacity(Math.round(frac * 100))
                        }

                        // ---- contrast (dynamic only) ----
                        ThemeSlider {
                            Layout.fillWidth: true
                            visible: root.thDynamic
                            label: "Contrast"
                            accent: root.cTertiary
                            value: (root.thContrast + 1) / 2
                            onCommitted: (frac) => root.setContrast(frac * 2 - 1)
                        }

                        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.cPrimary; opacity: 0.12 }

                        // ---- actions ----
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 40
                            radius: 11
                            color: wallMa.containsMouse
                                ? Qt.rgba(root.cPrimary.r, root.cPrimary.g, root.cPrimary.b, 0.16)
                                : root.cSurfaceHigh
                            opacity: root.themeBusy ? 0.4 : 1.0
                            Behavior on color { ColorAnimation { duration: 130 } }
                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 9
                                Text { text: "󰊨"; color: root.cPrimary; font.family: root.uiFont; font.pixelSize: 16 }
                                Text { text: "Random wallpaper"; color: root.cOnSurface; font.family: root.uiFont; font.pixelSize: 13; font.bold: true }
                            }
                            MouseArea {
                                id: wallMa
                                anchors.fill: parent
                                hoverEnabled: true
                                enabled: !root.themeBusy
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.randomWallpaper()
                            }
                        }

                        // Push to devbox (theme-manager push) with transient status
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 40
                            radius: 11
                            color: pushMa.containsMouse
                                ? Qt.rgba(root.cPrimary.r, root.cPrimary.g, root.cPrimary.b, 0.16)
                                : root.cSurfaceHigh
                            opacity: root.pushState === "busy" ? 0.6 : 1.0
                            Behavior on color { ColorAnimation { duration: 130 } }
                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 9
                                Text {
                                    text: root.pushState === "ok" ? "󰄬"
                                        : root.pushState === "fail" ? "󰅖" : "󰅢"
                                    color: root.pushState === "ok" ? root.cTertiary
                                        : root.pushState === "fail" ? root.cError : root.cPrimary
                                    font.family: root.uiFont; font.pixelSize: 16
                                }
                                Text {
                                    text: root.pushState === "busy" ? "Pushing…"
                                        : root.pushState === "ok" ? "Pushed"
                                        : root.pushState === "fail" ? "Push failed" : "Push to devbox"
                                    color: root.pushState === "ok" ? root.cTertiary
                                        : root.pushState === "fail" ? root.cError : root.cOnSurface
                                    font.family: root.uiFont; font.pixelSize: 13; font.bold: true
                                }
                            }
                            MouseArea {
                                id: pushMa
                                anchors.fill: parent
                                hoverEnabled: true
                                enabled: root.pushState !== "busy"
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.pushTheme()
                            }
                        }
                    }
                }
            }
        }
    }
}
