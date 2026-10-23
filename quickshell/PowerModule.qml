pragma ComponentBehavior: Bound
import QtQuick
import "StatusIcons.js" as Icons
import QtQuick.Layouts
ColumnLayout {
    id: control
    required property var shell
    required property string outputName
    property var systemState: shell.state
    property string pendingPower: ""
    onVisibleChanged: if (!visible) pendingPower = ""
    spacing: 12
    Text { text: "Питание"; color: control.shell.colors.fg; font.pixelSize: 14 }
    ThemedChoice {
        shell: control.shell; Layout.fillWidth: true
        property var values: control.systemState.profiles || []
        visible: values.length > 0; enabled: !!control.systemState.available
        model: values.map(p => ({"power-saver": "Экономия", balanced: "Сбалансированный", performance: "Производительный"})[p] || p)
        currentIndex: values.indexOf(control.systemState.profile)
        onActivated: control.shell.setProfile(values[currentIndex])
    }
    Text { text: control.systemState.battery && control.systemState.battery.percent >= 0 ? Icons.battery(control.systemState.battery) + " Батарея " + control.systemState.battery.percent + "% · " + control.systemState.battery.status : "Батарея недоступна"; color: control.systemState.battery && ["low", "critical"].includes(control.systemState.battery.level) ? control.shell.colors.power_color : control.shell.colors.fg_dim; font.pixelSize: 11 }
    Text {
        Layout.fillWidth: true
        objectName: "battery-remaining"
        visible: text !== ""
        text: control.systemState.battery ? (control.systemState.battery.remaining_text || "") : ""
        color: control.shell.colors.fg_dim; font.pixelSize: 11; wrapMode: Text.Wrap
    }
    RowLayout {
        ActionButton { shell: control.shell; text: "󰌾"; enabled: !!control.systemState.available; onClicked: control.shell.send("lock") }
        ActionButton { shell: control.shell; text: "Сон"; enabled: !!control.systemState.available; onClicked: control.pendingPower = "suspend" }
        ActionButton { shell: control.shell; text: "󰜉"; enabled: !!control.systemState.available; onClicked: control.pendingPower = "reboot" }
        ActionButton { shell: control.shell; text: "󰐥"; enabled: !!control.systemState.available; onClicked: control.pendingPower = "poweroff" }
    }
    RowLayout {
        visible: control.pendingPower !== ""
        ActionButton { shell: control.shell; text: "Подтвердить"; onClicked: { control.shell.send(control.pendingPower); control.pendingPower = "" } }
        ActionButton { shell: control.shell; text: "Отмена"; onClicked: control.pendingPower = "" }
    }
}
