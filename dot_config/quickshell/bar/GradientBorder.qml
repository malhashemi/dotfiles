import QtQuick

// Popup border: a solid background with a dark border, plus a horizontal
// dark -> bright(centre) -> dark "light zone" laid over the TOP edge only
// (matching the top bar's bright band). Place popup content as a SIBLING on top.
//
// Caller sets: anchors/size, radius, borderWidth, darkColor, brightColor,
// fillColor, and (optionally) opacity.
Rectangle {
    id: frame
    property color darkColor: "black"
    property color brightColor: "white"
    property color fillColor: "black"
    property int borderWidth: 2

    color: fillColor
    border.color: darkColor
    border.width: borderWidth

    // Light zone over the top border only. Skipped when there's no flat top
    // edge (e.g. a fully-rounded pill, where radius*2 >= width).
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: frame.radius
        anchors.rightMargin: frame.radius
        height: frame.borderWidth
        visible: frame.width > frame.radius * 2
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: frame.darkColor }
            GradientStop { position: 0.18; color: frame.darkColor }
            GradientStop { position: 0.35; color: frame.brightColor }
            GradientStop { position: 0.65; color: frame.brightColor }
            GradientStop { position: 0.82; color: frame.darkColor }
            GradientStop { position: 1.0; color: frame.darkColor }
        }
    }
}
