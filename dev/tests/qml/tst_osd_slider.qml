import QtQuick
import QtTest

Item {
    width: 100
    height: 160

    TestCase {
        name: "OsdSlider"
        when: windowShown

        function test_level_data() {
            return [
                {tag: "zero", level: 0, muted: false, label: "0%", fill: 0},
                {tag: "partial", level: 45, muted: false, label: "45%", fill: .45},
                {tag: "full", level: 100, muted: false, label: "100%", fill: 1},
                {tag: "above-max", level: 120, muted: false, label: "120%", fill: 1},
                {tag: "muted", level: 45, muted: true, label: "45%", fill: 0},
                {tag: "unavailable", level: -1, muted: false, label: "—", fill: 0}
            ]
        }

        function test_level(data) {
            const component = Qt.createComponent("../../../quickshell/OsdSlider.qml")
            compare(component.status, Component.Ready, component.errorString())
            const slider = createTemporaryObject(component, parent, {
                shown: true, level: data.level, muted: data.muted, icon: "●",
                surface: "#11111b", foreground: "#cdd6f4", accent: "#89b4fa"
            })
            verify(slider !== null)
            const label = findChild(slider, "osd-percentage")
            const track = findChild(slider, "osd-track")
            const fill = findChild(slider, "osd-fill")
            compare(label.text, data.label)
            verify(label.y + label.height <= track.y)
            verify(track.height > track.width)
            fuzzyCompare(fill.height / track.height, data.fill, .001)
            compare(fill.y + fill.height, track.height)
            compare(fill.color, Qt.color("#89b4fa"))
            slider.accent = "#db7700"
            compare(fill.color, Qt.color("#db7700"))
        }

        function test_slides_in_and_out() {
            const component = Qt.createComponent("../../../quickshell/OsdSlider.qml")
            compare(component.status, Component.Ready, component.errorString())
            const slider = createTemporaryObject(component, parent, {
                level: 70, icon: "●", surface: "#11111b",
                foreground: "#cdd6f4", accent: "#89b4fa"
            })
            verify(slider !== null)
            compare(slider.x, slider.width)
            slider.shown = true
            tryCompare(slider, "x", 0)
            slider.shown = false
            tryCompare(slider, "x", slider.width)
        }
    }
}
