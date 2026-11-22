pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: slider

    property bool shown: false
    required property real level
    property bool muted: false
    required property string icon
    required property color surface
    required property color foreground
    required property color accent
    readonly property bool onScreen: shown || x < width
    readonly property bool hasLevel: Number.isFinite(level) && level >= 0
    readonly property real fraction: hasLevel && !muted ? Math.min(level / 100, 1) : 0

    implicitWidth: 58
    implicitHeight: 140
    width: implicitWidth
    height: implicitHeight
    x: shown ? 0 : width
    visible: onScreen

    Behavior on x {
        NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
    }

    Rectangle {
        anchors.fill: parent
        color: slider.surface
        topLeftRadius: 19
        bottomLeftRadius: 19
        border.color: Qt.alpha(slider.foreground, .18)
        border.width: 1
    }

    Text {
        id: percentage
        objectName: "osd-percentage"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 9
        color: slider.foreground
        font.pixelSize: 11
        font.weight: Font.DemiBold
        text: slider.hasLevel ? Math.round(slider.level) + "%" : "—"
    }

    Rectangle {
        id: track
        objectName: "osd-track"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: percentage.bottom
        anchors.topMargin: 6
        anchors.bottom: glyph.top
        anchors.bottomMargin: 6
        width: 10
        radius: width / 2
        color: Qt.alpha(slider.foreground, .18)

        Rectangle {
            objectName: "osd-fill"
            anchors.bottom: parent.bottom
            width: parent.width
            height: parent.height * slider.fraction
            radius: Math.min(width, height) / 2
            color: slider.accent
        }
    }

    Text {
        id: glyph
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
        color: slider.foreground
        font.family: "JetBrainsMono Nerd Font"
        font.pixelSize: 21
        text: slider.icon
    }
}
