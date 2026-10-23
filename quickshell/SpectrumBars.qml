pragma ComponentBehavior: Bound
import QtQuick
Item {
    id: spectrum
    property var levels: []
    property color tint: "#89b4fa"
    implicitHeight: 64
    Row {
        anchors.fill: parent
        spacing: 3
        Repeater {
            model: 20
            Rectangle {
                required property int index
                objectName: "spectrum-bar-" + index
                width: Math.max(1, (spectrum.width-19*3)/20)
                height: Math.max(3, Math.min(spectrum.height, spectrum.height * Math.max(0, Math.min(1, Number(spectrum.levels[index]) || 0))))
                y: (spectrum.height-height)/2
                radius: width/2
                gradient: Gradient {
                    GradientStop { position: 0; color: spectrum.tint }
                    GradientStop { position: 1; color: Qt.alpha(spectrum.tint, 0.25) }
                }
                Behavior on height { NumberAnimation { duration: 65 } }
            }
        }
    }
}
