pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: center
    required property var shell
    required property string outputName
    property string page: "main"
    property string connectivitySection: ""
    function navigate(value) {
        if (value === "wifi" || value === "bluetooth") {
            page = "main"
            connectivitySection = value
        } else {
            page = value
        }
    }
    function toggleConnectivity(value) {
        page = "main"
        connectivitySection = connectivitySection === value ? "" : value
    }
    onVisibleChanged: if (!visible) { page = "main"; connectivitySection = "" }
    spacing: 12
    QuickSettingsHeader { shell: center.shell; outputName: center.outputName; visible: center.page === "main"; Layout.fillWidth: true }
    RowLayout {
        visible: center.page !== "main"
        Layout.fillWidth: true
        ActionButton { shell: center.shell; text: "‹ Назад"; onClicked: center.page = "main" }
        Text { Layout.fillWidth: true; text: ({wifi: "Wi-Fi", bluetooth: "Bluetooth", audio: "Звук и микрофон", vpn: "VPN", desktop: "Виджеты"})[center.page] || ""; color: center.shell.colors.fg; font.pixelSize: 16; elide: Text.ElideRight }
    }
    Loader {
        Layout.fillWidth: true
        Layout.preferredHeight: item ? item.implicitHeight : 0
        sourceComponent: center.page === "audio" ? audio : center.page === "vpn" ? vpn : center.page === "desktop" ? desktop : main
        Component { id: main; PanelModules { shell: center.shell; outputName: center.outputName; panel: "right"; navigator: center } }
        Component { id: audio; AudioModule { shell: center.shell; outputName: center.outputName; detailed: true } }
        Component { id: vpn; VpnModule { shell: center.shell; outputName: center.outputName } }
        Component { id: desktop; DesktopControlsModule { shell: center.shell; outputName: center.outputName } }
    }
}
