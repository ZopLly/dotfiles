import QtQuick
import QtTest
import "../../quickshell"
TestCase {
    name: "ConnectivityDrawers"
    width: 400; height: 900
    QtObject {
        id: fakeShell
        property var state: ({wifi: true, bluetooth: true, networks: [], bluetooth_devices: []})
        property var colors: ({fg: "#f3e7d0", fg_dim: "#d9ccb8", bg: "#17283a", surface: "#203447", accent: "#81b5d5", power_color: "#ff7777"})
        property int sends: 0
        function send() { sends++ }
    }
    Component { id: factory; ConnectivityModule { width: 380; shell: fakeShell; outputName: "test" } }
    function test_open_switch_close_without_radio_changes() {
        let drawer = createTemporaryObject(factory, this)
        verify(drawer)
        let originalHeight = drawer.implicitHeight
        drawer.toggleSection("wifi")
        compare(drawer.section, "wifi")
        tryVerify(() => drawer.implicitHeight > originalHeight + 100)
        drawer.toggleSection("bluetooth")
        compare(drawer.section, "bluetooth")
        drawer.toggleSection("bluetooth")
        compare(drawer.section, "")
        tryCompare(drawer, "implicitHeight", originalHeight)
        compare(fakeShell.sends, 0)
    }
}
