pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
Button {
    id: control
    required property var shell
    property bool selected: false
    property bool quiet: false
    implicitHeight: 40
    implicitWidth: Math.max(40, label.implicitWidth + 24)
    padding: 10
    background: Rectangle {
        radius: 12
        color: control.selected ? control.shell.colors.accent : (control.hovered ? (control.shell.colors.hover || control.shell.colors.fg_dim) : (control.quiet ? "transparent" : (control.shell.colors.surface || control.shell.colors.bg)))
        Behavior on color { ColorAnimation { duration: 130 } }
        opacity: control.enabled ? 1 : 0.4
    }
    contentItem: Text {
        id: label
        text: control.text
        font.family: "JetBrainsMono Nerd Font"
        font.pixelSize: 13
        color: control.selected ? control.shell.colors.bg : control.shell.colors.fg
        Behavior on color { ColorAnimation { duration: 130 } }
        opacity: control.enabled ? 1 : 0.45
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
