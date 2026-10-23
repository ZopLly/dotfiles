pragma ComponentBehavior: Bound
import QtQuick
Column {
    id: clock
    required property var shell
    spacing: 6
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: clock.shell.now.toLocaleDateString(Qt.locale("ru_RU"), "dddd").toUpperCase()
        color: clock.shell.colors.accent; font.pixelSize: 10; font.letterSpacing: 2
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: Qt.formatTime(clock.shell.now, "HH:mm")
        color: clock.shell.colors.fg; font.pixelSize: Math.min(60, clock.width/4.5); font.weight: Font.Light
    }
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        width: date.implicitWidth+24; height: 26; radius: 13
        color: Qt.alpha(clock.shell.colors.accent, .10)
        Text {
            id: date; anchors.centerIn: parent
            text: clock.shell.now.toLocaleDateString(Qt.locale("ru_RU"), "d MMMM")
            color: clock.shell.colors.fg_dim; font.pixelSize: 11
        }
    }
}
