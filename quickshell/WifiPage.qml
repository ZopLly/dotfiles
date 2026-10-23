pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "StatusIcons.js" as Icons
ColumnLayout {
    id: page
    required property var shell
    property real maxListHeight: 420
    property var stateData: shell.state
    property var networks: stateData.networks || []
    property var operation: (stateData.operations || {}).wifi || ({})
    spacing: 12
    Text { Layout.fillWidth: true; text: page.stateData.network || "Нет подключения"; textFormat: Text.PlainText; color: page.shell.colors.fg; font.pixelSize: 18; wrapMode: Text.Wrap }
    Text { Layout.fillWidth: true; text: !page.stateData.wifi ? "Wi-Fi выключен" : page.stateData.wifi_connection_state === "connecting" ? "Подключение…" : page.stateData.wifi_connected ? "Подключено · сигнал " + page.stateData.wifi_signal + "%" : "Нет соединения"; color: page.shell.colors.fg_dim; font.pixelSize: 12 }
    RowLayout {
        Layout.fillWidth: true
        ActionButton { shell: page.shell; Layout.fillWidth: true; text: page.stateData.wifi ? "Выключить" : "Включить"; selected: !!page.stateData.wifi; enabled: !!page.stateData.available && !!page.stateData.wifi_available && !page.operation.busy; onClicked: page.shell.send("wifi", {enabled: !page.stateData.wifi}) }
        ActionButton { shell: page.shell; text: "Обновить"; enabled: !!page.stateData.available && !!page.stateData.wifi && !page.operation.busy; onClicked: page.shell.send("wifi-rescan") }
    }
    Text { visible: !!page.operation.busy; text: page.operation.action === "wifi-connect" ? "Подключение · пароль запрашивается в терминале" : "Обновление сети…"; color: page.shell.colors.accent; Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11 }
    Text { visible: !!page.operation.error; text: page.operation.error || ""; textFormat: Text.PlainText; color: page.shell.colors.power_color; Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 12 }
    ListView {
        id: list
        Layout.fillWidth: true
        implicitHeight: Math.min(page.maxListHeight, contentHeight)
        clip: true; spacing: 6
        boundsBehavior: Flickable.StopAtBounds
        model: page.networks
        ScrollBar.vertical: ScrollBar { policy: list.contentHeight > list.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }
        delegate: ActionButton {
            required property var modelData
            shell: page.shell; width: list.width; height: 44
            text: modelData.ssid + " · " + modelData.signal + "%" + (modelData.security ? " · 󰌾" : "") + (modelData.active ? " · отключить" : "")
            selected: modelData.active
            enabled: !!page.stateData.available && !!page.stateData.wifi && !page.operation.busy
            onClicked: page.shell.send(modelData.active ? "wifi-disconnect" : "wifi-connect", {bssid: modelData.bssid})
        }
    }
    Text { visible: !page.networks.length; text: "Доступных сетей пока нет"; color: page.shell.colors.fg_dim; font.pixelSize: 12 }
    ActionButton { shell: page.shell; Layout.fillWidth: true; text: "Сохранённые профили / скрытая сеть…"; enabled: !!page.stateData.available; onClicked: page.shell.send("network-settings") }
}
