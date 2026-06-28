import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.CustomTheme

// Passive, click-through HUD overlay for voice-typer. Driven by the daemon over
// IPC (target "voice"). Never takes keyboard focus, so dictation keeps flowing
// into whatever app is focused. Compact pill, full-width transparent strip so
// the layer always has valid geometry.
PanelWindow {
    id: root

    property bool isOpen: false
    // states: loading | listening | locked | processing | ask | error | idle
    property string stateText: "listening"
    property string rawText: ""
    property string refinedText: ""
    property var levels: []
    readonly property int barCount: 20
    readonly property int barW: 6
    readonly property int barGap: 3
    // Gap (px) between the pill and the screen bottom when open, so the pill floats
    // clear of the focused window's border instead of sitting flush on the edge.
    readonly property int bottomGap: 56

    // derived state groups
    readonly property bool recording: stateText === "listening" || stateText === "locked"
    readonly property bool working: stateText === "processing" || stateText === "loading"

    function open() { rawText = ""; refinedText = ""; stateText = "listening"; isOpen = true }
    function close() { isOpen = false }

    function stateColor() {
        switch (stateText) {
        case "locked": return Theme.tertiary;
        case "processing": return Theme.secondary;
        case "loading": return Theme.secondary;
        case "error": return Theme.error;
        case "ask": return Theme.tertiary;
        case "idle": return Theme.outline;
        default: return Theme.primary;   // listening
        }
    }
    function stateLabel() {
        switch (stateText) {
        case "locked": return "Listening — locked";
        case "processing": return "Thinking…";
        case "loading": return "Loading model…";
        case "error": return "Error";
        case "ask": return "Needs input";
        case "idle": return "Done";
        default: return "Listening";
        }
    }

    // External control surface (daemon → HUD).
    IpcHandler {
        target: "voice"
        // NB: do not name a function `show` — it collides with the `qs ipc show`
        // subcommand and never dispatches. Use `reveal`.
        function reveal(): void { root.open() }
        function hide(): void { root.close() }
        function setState(s: string): void { root.stateText = s }
        function setRaw(t: string): void { root.rawText = t }
        function setRefined(t: string): void { root.refinedText = t }
        function ask(q: string): void { root.stateText = "ask"; root.refinedText = q }
        function reset(): void { root.rawText = ""; root.refinedText = "" }
        function reloadTheme(): void { Theme.reloadTheme() }
    }

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:voice-hud"
    exclusionMode: WlrLayershell.Ignore
    color: "transparent"
    anchors { left: true; right: true; bottom: true }
    mask: Region {}   // click-through

    // Grows with the pill so the layer surface always contains the (auto-sizing)
    // pill at its raised position (gap below + headroom above).
    implicitHeight: pill.height + root.bottomGap + 40
    visible: isOpen || slideAnim.running

    // Phase driver for the synthetic "thinking" wave (only while working).
    property real phase: 0
    NumberAnimation on phase {
        running: root.working
        loops: Animation.Infinite
        from: 0; to: 6.2832; duration: 1100
    }

    // cava (mic spectrum) — only runs while actively recording.
    Process {
        id: cavaProc
        command: [Quickshell.env("HOME") + "/.config/voice-typer/cava-mic"]
        running: root.isOpen && root.recording
        stdout: SplitParser {
            splitMarker: "\n"
            onRead: data => {
                const parts = data.split(";");
                const arr = [];
                for (let i = 0; i < parts.length; i++) {
                    const v = parseInt(parts[i]);
                    if (!isNaN(v)) arr.push(v);
                }
                if (arr.length > 0) root.levels = arr;
            }
        }
    }

    Item {
        id: pill
        anchors.horizontalCenter: parent.horizontalCenter
        width: 460
        height: content.implicitHeight + 28   // grows to fit the transcript

        anchors.bottom: parent.bottom
        anchors.bottomMargin: root.isOpen ? root.bottomGap : -(height + 40)
        Behavior on anchors.bottomMargin {
            NumberAnimation { id: slideAnim; duration: 300; easing.type: Easing.OutQuint }
        }

        // Soft drop shadow behind the frame (matches the bar's Calendar/Power popups).
        RectangularShadow {
            anchors.fill: frame
            radius: frame.radius
            blur: 15
            color: Qt.rgba(0, 0, 0, 0.4)
        }
        // Frame matched to the quickshell bar popups: solid fill + dark border with a
        // bright top "light zone"; the bright centre follows the HUD state colour.
        GradientBorder {
            id: frame
            anchors.fill: parent
            radius: 10
            borderWidth: 2
            darkColor: Theme.on_primary
            brightColor: root.stateColor()
            fillColor: Theme.background
            opacity: 0.95
        }

        Column {
            id: content
            anchors.centerIn: parent
            width: parent.width - 32
            spacing: 8

            Row {
                spacing: 8
                anchors.horizontalCenter: parent.horizontalCenter
                Rectangle {
                    width: 9; height: 9; radius: 4.5
                    anchors.verticalCenter: parent.verticalCenter
                    color: root.stateColor()
                    SequentialAnimation on opacity {
                        running: root.recording || root.working
                        loops: Animation.Infinite
                        NumberAnimation { from: 1.0; to: 0.3; duration: 600 }
                        NumberAnimation { from: 0.3; to: 1.0; duration: 600 }
                    }
                }
                Text {
                    text: root.stateLabel()
                    color: Theme.on_surface
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    font.bold: true
                }
            }

            // Equalizer: cava spectrum while recording; synthetic wave while
            // thinking/loading; flat dots when idle.
            Item {
                id: eq
                width: root.barCount * (root.barW + root.barGap) - root.barGap
                height: 24
                anchors.horizontalCenter: parent.horizontalCenter
                Repeater {
                    model: root.barCount
                    Rectangle {
                        width: root.barW
                        radius: root.barW / 2
                        x: index * (root.barW + root.barGap)
                        color: root.stateColor()
                        height: {
                            if (root.recording) {
                                const lvl = index < root.levels.length ? root.levels[index] : 0;
                                return Math.max(root.barW, lvl / 100 * eq.height);
                            }
                            if (root.working) {
                                const w = Math.sin(root.phase + index * 0.5) * 0.5 + 0.5;
                                return root.barW + w * (eq.height - root.barW) * 0.85;
                            }
                            return root.barW;  // flat
                        }
                        y: eq.height - height
                        opacity: root.recording ? (0.55 + 0.45 * Math.min(1, (index < root.levels.length ? root.levels[index] : 0) / 60))
                                                 : (root.working ? 0.9 : 0.4)
                        Behavior on height { NumberAnimation { duration: 70 } }
                    }
                }
            }

            Text {
                id: txt
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                // Typewriter for the live raw transcript; the single correction
                // (refinedText) just swaps in (no retype — model runs once).
                property bool refined: root.refinedText !== ""
                property string _typed: ""
                text: refined ? root.refinedText : _typed
                visible: text !== ""
                color: refined ? Theme.on_surface : Theme.on_surface_variant
                font.family: Theme.fontFamily
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                maximumLineCount: 8
                elide: Text.ElideRight
                Behavior on opacity { NumberAnimation { duration: 120 } }
                Timer {
                    interval: 8; repeat: true
                    running: !txt.refined && txt._typed.length < root.rawText.length
                             && root.rawText.indexOf(txt._typed) === 0
                    onTriggered: txt._typed = root.rawText.substring(0, txt._typed.length + 3)
                }
                Connections {
                    target: root
                    function onRawTextChanged() {
                        if (root.rawText.indexOf(txt._typed) !== 0)
                            txt._typed = ""   // raw reset/replaced -> start over
                    }
                }
            }
        }
    }
}
