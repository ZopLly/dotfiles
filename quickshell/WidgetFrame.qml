pragma ComponentBehavior: Bound
import QtQuick
Rectangle {
    id: frame
    required property var shell
    property bool editing: false
    radius: 24
    gradient: Gradient {
        GradientStop { position: 0; color: Qt.tint(frame.shell.colors.bg_modules, Qt.alpha(frame.shell.colors.accent, .075)) }
        GradientStop { position: 1; color: frame.shell.colors.bg_modules }
    }
    border.width: editing ? 2 : 1
    border.color: editing ? shell.colors.accent : Qt.alpha(shell.colors.fg, .13)
    Rectangle {
        width: Math.min(38, parent.width/5); height: 3; radius: 1.5
        anchors { top: parent.top; topMargin: 1; horizontalCenter: parent.horizontalCenter }
        color: Qt.alpha(frame.shell.colors.accent, .65)
    }
}
