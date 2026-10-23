pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
SpectrumBars {
    id: visualizer
    required property var shell
    property bool active: false
    tint: shell.colors.cava_color || shell.colors.accent
    Process {
        command: ["python3", Quickshell.shellDir+"/../waybar/scripts/cava_stream.py", "--json"]
        running: visualizer.active && !visualizer.shell.state.preview
        stdout: SplitParser {
            onRead: data => {
                try {
                    let values = JSON.parse(data)
                    if (Array.isArray(values)) visualizer.levels = values
                } catch(e) { visualizer.levels = [] }
            }
        }
        onExited: visualizer.levels = []
    }
}
