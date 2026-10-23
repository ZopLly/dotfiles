pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: control
    required property var shell
    required property string outputName
    property var systemState: shell.state
    property string pendingPower: ""
    onVisibleChanged: if (!visible) pendingPower = ""
    spacing: 12
    Text { text: "VPN"; color: control.shell.colors.fg; font.pixelSize: 14 }
    ActionButton {
        objectName: "open-happ"
        shell: control.shell; Layout.fillWidth: true; text: "Открыть Happ"
        enabled: (control.shell.applications.entries || []).some(app => app.id === "Happ.desktop")
        onClicked: control.shell.applications.act("launch", "Happ.desktop")
    }
    Text { Layout.fillWidth: true; text: "Подключение и сервер выбираются в приложении Happ"; wrapMode: Text.Wrap; color: control.shell.colors.fg_dim; font.pixelSize: 11 }
    Repeater {
        model: control.systemState.vpns || []
        ActionButton { required property var modelData; shell: control.shell; Layout.fillWidth: true; text: modelData.name; selected: modelData.active; onClicked: control.shell.send("vpn", {uuid: modelData.uuid, enabled: !modelData.active}) }
    }
    Text { visible: !(control.systemState.vpns || []).length; text: "Нет профилей VPN в NetworkManager"; color: control.shell.colors.fg_dim; font.pixelSize: 11 }
}
