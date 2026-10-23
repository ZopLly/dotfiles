pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Wayland
import "StatusIcons.js" as Icons
PanelWindow {
    id: osd
    required property var shell
    required property string outputName
    visible: shell.osdKind !== "" && outputName === shell.osdScreen
    anchors { bottom: true }
    margins.bottom: 72
    implicitWidth: 260; implicitHeight: 66
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: Region {}
    Rectangle {
        anchors.fill: parent
        color: osd.shell.colors.bg_modules; radius: 22
        border.width: 1; border.color: osd.shell.colors.accent
        Row {
            anchors.centerIn: parent; spacing: 14
            Text {
                font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 24
                color: osd.shell.colors.fg
                text: osd.shell.osdKind === "brightness" ? "󰃠" : osd.shell.osdKind.startsWith("mic") ? (osd.shell.state.mic_muted ? "󰍭" : "󰍬") : Icons.volume(osd.shell.state.volume, osd.shell.state.muted)
            }
            Text {
                color: osd.shell.colors.fg; font.pixelSize: 20
                text: osd.shell.osdKind === "brightness" ? osd.shell.state.brightness + "%" : osd.shell.osdKind.startsWith("mic") ? (osd.shell.state.mic_muted ? "Микрофон выкл." : osd.shell.state.mic_volume + "%") : osd.shell.state.muted ? "Без звука" : osd.shell.state.volume + "%"
            }
        }
    }
}
