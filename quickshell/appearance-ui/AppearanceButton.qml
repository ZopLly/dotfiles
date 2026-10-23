pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
Button {
    id: control
    padding: 11
    leftPadding: 16; rightPadding: 16
    font.pixelSize: 14
    background: Rectangle {
        radius: 10
        color: control.highlighted || control.checked ? control.palette.highlight : control.palette.button
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? control.palette.highlight : Qt.rgba(0.5,0.5,0.5,0.2)
        opacity: control.enabled ? 1 : 0.5
    }
    contentItem: Text {
        text: control.text; font: control.font
        color: control.highlighted || control.checked ? control.palette.highlightedText : control.palette.buttonText
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
