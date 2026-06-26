import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland // <-- Added native Hyprland integration
import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import QtQuick.Effects

PanelWindow {
    id: root

    // Colors + font supplied by the bar.
    property color cPrimary: "#ffb4a5"
    property color cOnPrimary: "#3b0b03"
    property color cBg: "#1a1110"
    property string uiFont: "JetBrainsMono Nerd Font"

    // Open and close the menu; called by the bar's power button.
    function toggle() { root.isOpen = !root.isOpen }
    
    // --- 1. OVERLAY & WAYLAND FIXES ---
    WlrLayershell.layer: WlrLayer.Overlay
    exclusionMode: WlrLayershell.Ignore 
    
    implicitWidth: panelBg.implicitWidth + 40
    implicitHeight: panelBg.implicitHeight + 40
    color: "transparent"

    anchors {
        right: true
    }

    // --- CLICK OUTSIDE TO CLOSE (Native Hyprland) ---
    HyprlandFocusGrab {
        windows: [root]
        active: root.isOpen
        onCleared: {
            if (root.isOpen) {
                root.isOpen = false
            }
        }
    }

    // --- HANDLE ESCAPE SHORTCUT ---
    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (root.isOpen) {
                root.isOpen = false
            }
        }
    }

    // --- 2. ANIMATION LOGIC (FIXED) ---
    property bool isOpen: false
    
    // Keep the window mapped to the screen while the animation is playing
    visible: isOpen || slideAnim.running
    
    margins {
        right: root.currentMargin
    }

    // Ternary operator: If open, set to 20. If closed, set to -150.
    property real currentMargin: isOpen ? 0 : -170 

    // This automatically animates currentMargin whenever it changes!
    Behavior on currentMargin {
        NumberAnimation {
            id: slideAnim
            duration: 350
            easing.type: Easing.OutQuint 
        }
    }

    // ==========================================
    // MAIN PANEL BACKGROUND (The Pill Shape)
    // ==========================================
    Item {
        id: panelBg
        implicitWidth: 80 
        implicitHeight: buttonLayout.implicitHeight + 40 
        anchors.centerIn: parent

        RectangularShadow {
            id: shadow
            anchors.fill: mainBgRect
            radius: mainBgRect.radius
            blur: 15
            color: Qt.rgba(0, 0, 0, 0.4)
        }

        GradientBorder {
            id: mainBgRect
            anchors.fill: parent
            darkColor: cOnPrimary
            brightColor: cPrimary
            fillColor: cBg
            borderWidth: 2
            radius: 40
            opacity: 0.9 // Only the background is transparent
        }

        // ==========================================
        // BUTTON LAYOUT
        // ==========================================
        ColumnLayout {
            id: buttonLayout
            anchors.centerIn: parent
            spacing: 20 

            component PowerButton: Rectangle {
                id: btn
                property string iconTxt: ""
                property string cmd: ""
                
                // Add a custom signal to the component
                signal clicked()

                implicitWidth: 50
                implicitHeight: 50
                radius: 25 
                
                color: mouseArea.containsMouse ? cPrimary : "transparent"
                border.color: cPrimary
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: btn.iconTxt
                    font.family: uiFont
                    font.pixelSize: 20
                    color: mouseArea.containsMouse ? cBg : cPrimary
                }

                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        // 1. Emit our custom clicked signal
                        btn.clicked()
                        // 2. Trigger the slide-out animation!
                        root.isOpen = false 
                    }
                }
            }

            PowerButton { 
                iconTxt: ""; 
                onClicked: { Quickshell.execDetached(["bash", "-c", Quickshell.env("HOME") + "/.config/quickshell/bar/scripts/power.sh -l"]) } 
            }
            PowerButton { 
                iconTxt: ""; 
                onClicked: { Quickshell.execDetached(["bash", "-c", Quickshell.env("HOME") + "/.config/quickshell/bar/scripts/power.sh -s"]) } 
            }
            PowerButton { 
                iconTxt: ""; 
                onClicked: { Quickshell.execDetached(["bash", "-c", Quickshell.env("HOME") + "/.config/quickshell/bar/scripts/power.sh -e"]) } 
            }
            PowerButton { 
                iconTxt: ""; 
                onClicked: { Quickshell.execDetached(["bash", "-c", Quickshell.env("HOME") + "/.config/quickshell/bar/scripts/power.sh -r"]) } 
            }
            PowerButton { 
                iconTxt: ""; 
                onClicked: { Quickshell.execDetached(["bash", "-c", Quickshell.env("HOME") + "/.config/quickshell/bar/scripts/power.sh -p"]) } 
            }
        }
    }
}