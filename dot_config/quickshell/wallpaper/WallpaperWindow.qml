import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Qt.labs.folderlistmodel
import Qt5Compat.GraphicalEffects
import QtQuick.Effects
import qs.CustomTheme

PanelWindow {
    id: root

    // --- WAYLAND CONFIGURATION ---
    WlrLayershell.layer: WlrLayer.Overlay
    exclusionMode: WlrLayershell.Ignore

    implicitWidth: 420
    color: "transparent"

    anchors {
        left: true
        top: true
        bottom: true
    }

    margins {
        top: 67
        bottom: 0
    }

    // --- CLICK OUTSIDE TO CLOSE ---
    HyprlandFocusGrab {
        windows: [root]
        active: root.isOpen
        onCleared: {
            if (root.isOpen)
                root.isOpen = false
        }
    }

    // --- ESCAPE KEY LISTENER ---
    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (root.isOpen)
                root.isOpen = false
        }
    }

    // --- ANIMATION LOGIC ---
    property bool isOpen: false
    visible: isOpen || slideAnim.running

    margins { left: root.currentMargin }
    property real currentMargin: isOpen ? 0 : -470

    Behavior on currentMargin {
        NumberAnimation {
            id: slideAnim
            duration: 250
            easing.type: Easing.OutQuint
        }
    }

    onIsOpenChanged: {
        if (isOpen) {
            root.refreshFolder()
            root.refreshTransition()
        }
    }

    // --- IPC HANDLER ---
    IpcHandler {
        target: "wallpaper"
        function toggle(): void { root.isOpen = !root.isOpen }
        function open(): void { root.isOpen = true }
        function close(): void { root.isOpen = false }
    }

    // --- THEME-SYSTEM DRIVEN STATE ---
    // Wallpaper folder is resolved per current theme + OS by the theme-system.
    property string wallpaperManager: Quickshell.env("HOME") + "/.config/theme-system/scripts/wallpaper-manager.py"
    property string wallpaperFolder: Quickshell.env("HOME") + "/Pictures/Wallpapers"

    property var transitionTypes: [
        "none", "simple", "fade", "left", "right", "top", "bottom",
        "wipe", "wave", "grow", "outer", "random"
    ]
    property var transitionPositions: [
        "center", "top", "left", "right", "bottom",
        "top-left", "top-right", "bottom-left", "bottom-right"
    ]
    property var transitionAngles: ["0", "45", "90", "135", "180", "225", "270", "315"]

    property string transitionType: "simple"
    property string transitionPos: "center"
    property string transitionAngle: "45"

    readonly property bool typeUsesPos: transitionType === "grow" || transitionType === "outer"
    readonly property bool typeUsesAngle: transitionType === "wipe" || transitionType === "wave"

    function refreshFolder(): void {
        folderProc.running = false
        folderProc.running = true
    }

    function refreshTransition(): void {
        transitionProc.running = false
        transitionProc.running = true
    }

    function persistTransitionType(t): void {
        root.transitionType = t
        Quickshell.execDetached(["bash", "-c",
            root.wallpaperManager + " transition --type '" + t + "'"])
    }
    function persistTransitionPos(p): void {
        root.transitionPos = p
        Quickshell.execDetached(["bash", "-c",
            root.wallpaperManager + " transition --pos '" + p + "'"])
    }
    function persistTransitionAngle(a): void {
        root.transitionAngle = a
        Quickshell.execDetached(["bash", "-c",
            root.wallpaperManager + " transition --angle '" + a + "'"])
    }

    function transitionArgs(): string {
        return " --transition '" + root.transitionType + "'"
            + " --pos '" + root.transitionPos + "'"
            + " --angle '" + root.transitionAngle + "'"
    }

    function setWallpaper(path): void {
        Quickshell.execDetached(["bash", "-c",
            root.wallpaperManager + " set '" + path + "'" + root.transitionArgs()])
        root.isOpen = false
    }

    function randomWallpaper(): void {
        Quickshell.execDetached(["bash", "-c",
            root.wallpaperManager + " random" + root.transitionArgs()])
        root.isOpen = false
    }

    Process {
        id: folderProc
        command: ["bash", "-c", root.wallpaperManager + " current-folder"]
        stdout: StdioCollector {
            onStreamFinished: {
                const out = this.text.trim()
                if (out !== "")
                    root.wallpaperFolder = out
            }
        }
    }

    Process {
        id: transitionProc
        command: ["bash", "-c", root.wallpaperManager + " transition --json"]
        stdout: StdioCollector {
            onStreamFinished: {
                const out = this.text.trim()
                if (out === "")
                    return
                try {
                    const s = JSON.parse(out)
                    if (s.type && root.transitionTypes.indexOf(s.type) !== -1)
                        root.transitionType = s.type
                    if (s.pos && root.transitionPositions.indexOf(s.pos) !== -1)
                        root.transitionPos = s.pos
                    if (s.angle && root.transitionAngles.indexOf(String(s.angle)) !== -1)
                        root.transitionAngle = String(s.angle)
                } catch (e) {
                    console.log("transition JSON parse failed: " + e)
                }
            }
        }
    }

    Component.onCompleted: {
        root.refreshFolder()
        root.refreshTransition()
    }

    // --- REUSABLE COMPONENTS ---
    component MenuRow: MenuItem {
        id: control
        contentItem: Text {
            text: control.text
            font.family: Theme.fontFamily
            font.pixelSize: 14
            color: control.highlighted ? Theme.background : Theme.primary
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            implicitWidth: 200
            implicitHeight: 36
            color: control.highlighted ? Theme.primary : "transparent"
            radius: 4
        }
    }

    component SettingsWheel: Button {
        implicitWidth: 28
        implicitHeight: 28
        text: "\uf013"
        background: Rectangle { color: "transparent" }
        contentItem: Text {
            text: parent.text
            color: Theme.primary
            font.family: Theme.fontFamily
            font.pixelSize: 18
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
    }

    component ThemedCombo: ComboBox {
        id: combo
        Layout.fillWidth: true

        delegate: ItemDelegate {
            id: itemDelegate
            width: combo.width
            contentItem: Text {
                text: modelData
                color: itemDelegate.highlighted ? Theme.background : Theme.primary
                font.family: Theme.fontFamily
                font.pixelSize: 14
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
            background: Rectangle {
                color: itemDelegate.highlighted ? Theme.primary : "transparent"
                radius: 4
            }
            highlighted: combo.highlightedIndex === index
        }

        contentItem: Text {
            leftPadding: 12
            text: combo.displayText
            font.family: Theme.fontFamily
            font.pixelSize: 14
            color: Theme.primary
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }

        background: Rectangle {
            implicitHeight: 36
            color: Theme.background
            border.color: Theme.primary
            border.width: 1
            radius: 10
        }

        popup: Popup {
            y: combo.height + 2
            width: combo.width
            implicitHeight: contentItem.contentHeight > 250 ? 250 : contentItem.contentHeight
            padding: 4
            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: combo.popup.visible ? combo.delegateModel : null
                currentIndex: combo.highlightedIndex
                ScrollIndicator.vertical: ScrollIndicator {}
            }
            background: Rectangle {
                color: Theme.background
                border.color: Theme.primary
                border.width: 1
                radius: 8
            }
        }
    }

    Item {
        anchors.fill: parent
        anchors.margins: 20

        RectangularShadow {
            id: shadow
            anchors.fill: mainBgRect
            radius: mainBgRect.radius
            blur: 15
            color: Qt.rgba(Theme.shadow.r, Theme.shadow.g, Theme.shadow.b, 0.4)
        }

        Rectangle {
            id: mainBgRect
            anchors.fill: parent
            color: Theme.background
            border.color: Theme.primary
            border.width: 2
            radius: 10
            opacity: 0.95
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                // --- HEADER (Search + Settings) ---
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 5
                    spacing: 10

                    TextField {
                        id: searchInput
                        placeholderText: "Search image"
                        color: Theme.primary
                        font.pixelSize: 14
                        padding: 8
                        Layout.fillWidth: true
                        horizontalAlignment: TextInput.AlignHCenter
                        background: Rectangle {
                            anchors.fill: parent
                            color: Theme.background
                            radius: 10
                            border.color: Theme.primary
                            border.width: 1
                        }
                    }

                    SettingsWheel {
                        onClicked: wallpaperMenu.open()

                        Menu {
                            id: wallpaperMenu
                            y: parent.height
                            implicitWidth: 220
                            padding: 8
                            background: Rectangle {
                                color: Theme.background
                                border.color: Theme.primary
                                border.width: 1
                                radius: 8
                            }

                            MenuRow {
                                text: "Random Wallpaper"
                                onClicked: root.randomWallpaper()
                            }
                            MenuRow {
                                text: "Reload Images"
                                onClicked: root.refreshFolder()
                            }
                            MenuRow {
                                text: advancedOptions.visible ? "Hide Advanced Options" : "Show Advanced Options"
                                onClicked: advancedOptions.visible = !advancedOptions.visible
                            }
                        }
                    }
                }

                // --- ADVANCED OPTIONS (transition: type + position + angle) ---
                ColumnLayout {
                    id: advancedOptions
                    Layout.fillWidth: true
                    Layout.topMargin: 5
                    spacing: 10
                    visible: false

                    Label {
                        text: "Transition Type"
                        color: Theme.primary
                        font.family: Theme.fontFamily
                    }
                    ThemedCombo {
                        model: root.transitionTypes
                        currentIndex: root.transitionTypes.indexOf(root.transitionType)
                        onActivated: (index) => root.persistTransitionType(root.transitionTypes[index])
                    }

                    Label {
                        text: "Circle Position"
                        color: Theme.primary
                        font.family: Theme.fontFamily
                        visible: root.typeUsesPos
                    }
                    ThemedCombo {
                        visible: root.typeUsesPos
                        model: root.transitionPositions
                        currentIndex: root.transitionPositions.indexOf(root.transitionPos)
                        onActivated: (index) => root.persistTransitionPos(root.transitionPositions[index])
                    }

                    Label {
                        text: "Angle (°)"
                        color: Theme.primary
                        font.family: Theme.fontFamily
                        visible: root.typeUsesAngle
                    }
                    ThemedCombo {
                        visible: root.typeUsesAngle
                        model: root.transitionAngles
                        currentIndex: root.transitionAngles.indexOf(root.transitionAngle)
                        onActivated: (index) => root.persistTransitionAngle(root.transitionAngles[index])
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: Theme.primary
                    opacity: 0.3
                }

                Text {
                    id: emptyMsg
                    visible: false
                    Layout.fillWidth: true
                    color: Theme.primary
                    font.family: Theme.fontFamily
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    text: "Wallpaper folder is either empty or invalid."
                }

                // --- IMAGE GRID ---
                GridView {
                    id: grid
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    cacheBuffer: 3000
                    reuseItems: true
                    cellWidth: width / 2
                    cellHeight: cellWidth * 0.80

                    ScrollBar.vertical: ScrollBar { interactive: true }

                    model: FolderListModel {
                        folder: "file://" + root.wallpaperFolder
                        showDirs: false
                        caseSensitive: false
                        sortField: FolderListModel.Name
                        nameFilters: {
                            const s = searchInput.text.trim()
                            if (s === "")
                                return ["*.jpg", "*.jpeg", "*.png"]
                            return ["*" + s + "*.jpg", "*" + s + "*.jpeg", "*" + s + "*.png"]
                        }
                        onCountChanged: {
                            emptyMsg.visible = (count === 0 && this.status === FolderListModel.Ready)
                        }
                    }

                    delegate: Item {
                        width: grid.cellWidth
                        height: grid.cellHeight

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 8
                            color: Theme.secondary
                            border.color: mouseArea.containsMouse ? Theme.primary : "transparent"
                            border.width: 2
                            radius: 10
                            clip: true

                            Rectangle {
                                id: contentMask
                                anchors.fill: parent
                                anchors.margins: 2
                                radius: 8
                                visible: false
                            }

                            Item {
                                anchors.fill: parent
                                anchors.margins: 2
                                layer.enabled: true
                                layer.effect: OpacityMask { maskSource: contentMask }

                                BusyIndicator {
                                    anchors.centerIn: parent
                                    width: 30
                                    height: 30
                                    running: thumbnail.status === Image.Loading
                                    opacity: running ? 0.5 : 0.0
                                }

                                Image {
                                    id: thumbnail
                                    anchors.fill: parent
                                    source: "file://" + model.filePath
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    sourceSize.width: 250
                                    sourceSize.height: 250
                                    opacity: status === Image.Ready ? 1.0 : 0.0
                                    Behavior on opacity {
                                        NumberAnimation { duration: 350; easing.type: Easing.OutCubic }
                                    }
                                }

                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    height: 22
                                    color: "#aa000000"
                                    Text {
                                        anchors.centerIn: parent
                                        text: model.fileName
                                        color: "white"
                                        font.pixelSize: 11
                                        elide: Text.ElideRight
                                        width: parent.width - 8
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                            }

                            MouseArea {
                                id: mouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.setWallpaper(model.filePath)
                            }
                        }
                    }
                }
            }
        }
    }
}
