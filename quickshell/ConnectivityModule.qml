pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "StatusIcons.js" as Icons
ColumnLayout {
    id: control
    required property var shell
    required property string outputName
    property var navigator: null
    property var systemState: shell.state
    property string section: navigator ? navigator.connectivitySection : ""
    function toggleSection(value) {
        if (navigator) navigator.toggleConnectivity(value)
        else section = section === value ? "" : value
    }
    spacing: 8
    RowLayout {
        Layout.fillWidth: true
        ActionButton { shell: control.shell; Layout.fillWidth: true; text: Icons.wifi(control.systemState) + " Wi-Fi " + (control.section === "wifi" ? "⌃" : "⌄"); selected: !!control.systemState.wifi; onClicked: control.toggleSection("wifi") }
        ActionButton { shell: control.shell; Layout.fillWidth: true; text: Icons.bluetooth(control.systemState) + " Bluetooth " + (control.section === "bluetooth" ? "⌃" : "⌄"); selected: !!control.systemState.bluetooth; onClicked: control.toggleSection("bluetooth") }
    }
    Text { Layout.fillWidth: true; text: control.systemState.network || "Нет подключения"; textFormat: Text.PlainText; elide: Text.ElideRight; color: control.shell.colors.fg_dim; font.pixelSize: 11 }
    Rectangle {
        id: drawer
        Layout.fillWidth: true
        implicitHeight: control.section ? contents.implicitHeight + 24 : 0
        Layout.preferredHeight: implicitHeight
        visible: implicitHeight > 0
        clip: true
        radius: 16
        color: control.shell.colors.surface || control.shell.colors.bg
        Behavior on implicitHeight { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
        ColumnLayout {
            id: contents
            x: 12; y: 12
            width: parent.width - 24
            spacing: 10
            RowLayout {
                Layout.fillWidth: true
                Text { Layout.fillWidth: true; text: control.section === "wifi" ? "Wi-Fi" : "Bluetooth"; color: control.shell.colors.fg; font.pixelSize: 15 }
                ActionButton { shell: control.shell; text: "Свернуть ⌃"; quiet: true; onClicked: control.toggleSection(control.section) }
            }
            Loader {
                Layout.fillWidth: true
                Layout.preferredHeight: item ? item.implicitHeight : 0
                active: !!control.section
                sourceComponent: control.section === "wifi" ? wifiDetails : bluetoothDetails
                Component { id: wifiDetails; WifiPage { shell: control.shell; maxListHeight: 260 } }
                Component { id: bluetoothDetails; BluetoothPage { shell: control.shell; maxListHeight: 260 } }
            }
        }
    }
    ActionButton { shell: control.shell; Layout.fillWidth: true; text: "Не беспокоить"; selected: !!control.systemState.dnd; enabled: !!control.systemState.available; onClicked: control.shell.send("dnd", {enabled: !control.systemState.dnd}) }
}
