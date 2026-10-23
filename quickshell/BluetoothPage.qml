pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: page
    required property var shell
    property real maxListHeight: 420
    property var stateData: shell.state
    property var operation: (stateData.operations || {}).bluetooth || ({})
    property var devices: stateData.bluetooth_devices || []
    property var orderedDevices: devices.slice().sort((a,b) => (a.connected ? 0 : a.paired ? 1 : 2) - (b.connected ? 0 : b.paired ? 1 : 2))
    spacing: 12
    RowLayout {
        Layout.fillWidth: true
        ActionButton { shell: page.shell; Layout.fillWidth: true; text: page.stateData.bluetooth ? "Bluetooth включён" : "Bluetooth выключен"; selected: !!page.stateData.bluetooth; enabled: !!page.stateData.available && !!page.stateData.bluetooth_available && !page.operation.busy; onClicked: page.shell.send("bluetooth", {enabled: !page.stateData.bluetooth}) }
        ActionButton { shell: page.shell; text: "Поиск"; enabled: !!page.stateData.available && !!page.stateData.bluetooth && !page.operation.busy; onClicked: page.shell.send("bluetooth-scan") }
    }
    Text { visible: !page.stateData.bluetooth_available; text: "Адаптер недоступен"; color: page.shell.colors.fg_dim; font.pixelSize: 12 }
    Text { visible: !!page.operation.busy; text: page.operation.action === "bluetooth-scan" ? "Поиск устройств · до 10 секунд…" : page.operation.action === "bluetooth-pair" ? "Сопряжение · подтвердите PIN, если появится запрос…" : "Подключение / отключение…"; color: page.shell.colors.accent; Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 12 }
    Text { visible: !!page.operation.error; text: page.operation.error || ""; textFormat: Text.PlainText; color: page.shell.colors.power_color; Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 12 }
    ListView {
        id: list
        Layout.fillWidth: true
        implicitHeight: Math.min(page.maxListHeight, contentHeight)
        model: page.orderedDevices; spacing: 6; clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: list.contentHeight > list.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }
        delegate: Column {
            required property var modelData
            required property int index
            width: list.width; spacing: 4
            Text { visible: parent.index === 0 || page.orderedDevices[parent.index-1].category !== parent.modelData.category; text: parent.modelData.category; color: page.shell.colors.fg_dim; font.pixelSize: 12; height: 28; verticalAlignment: Text.AlignVCenter }
            Text { width: parent.width; text: parent.modelData.name; textFormat: Text.PlainText; color: page.shell.colors.fg; elide: Text.ElideRight; font.pixelSize: 13 }
            ActionButton {
                shell: page.shell; width: parent.width; height: 40
                text: parent.modelData.connecting ? "Выполняется…" : parent.modelData.connected ? "Отключить" : parent.modelData.paired ? "Подключить" : "Сопрячь"
                selected: parent.modelData.connected
                enabled: !!page.stateData.available && !!page.stateData.bluetooth && !page.operation.busy
                onClicked: page.shell.send(parent.modelData.paired || parent.modelData.connected ? "bluetooth-device" : "bluetooth-pair", {address: parent.modelData.address, enabled: !parent.modelData.connected})
            }
        }
    }
    Text { visible: !page.devices.length; text: "Устройств нет · запустите поиск"; color: page.shell.colors.fg_dim; font.pixelSize: 12 }
    ActionButton { shell: page.shell; Layout.fillWidth: true; text: "Blueman · PIN и дополнительные настройки…"; enabled: !!page.stateData.available; onClicked: page.shell.send("bluetooth-settings") }
}
