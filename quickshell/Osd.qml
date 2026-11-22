pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Wayland
import "StatusIcons.js" as Icons

PanelWindow {
    id: osd
    required property var shell
    required property string outputName
    readonly property bool microphone: shell.osdAudioKind.startsWith("mic_")

    visible: outputName === shell.osdScreen && (brightness.onScreen || audio.onScreen)
    anchors { right: true }
    implicitWidth: brightness.implicitWidth
    implicitHeight: audio.y + audio.implicitHeight
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: Region {}

    Item {
        anchors.fill: parent
        clip: true

        OsdSlider {
            id: brightness
            shown: osd.shell.osdBrightness
            level: osd.shell.state.brightness ?? -1
            icon: "󰃠"
            surface: osd.shell.colors.bg_modules
            foreground: osd.shell.colors.fg
            accent: osd.shell.colors.accent
        }

        OsdSlider {
            id: audio
            y: brightness.height + 8
            shown: osd.shell.osdAudio
            level: (osd.microphone ? osd.shell.state.mic_volume : osd.shell.state.volume) ?? -1
            muted: (osd.microphone ? osd.shell.state.mic_muted : osd.shell.state.muted) ?? false
            icon: osd.microphone ? (muted ? "󰍭" : "󰍬") : Icons.volume(level, muted)
            surface: osd.shell.colors.bg_modules
            foreground: osd.shell.colors.fg
            accent: osd.shell.colors.accent
        }
    }
}
