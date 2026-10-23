pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: control
    required property var shell
    required property string outputName
    property var systemState: shell.state
    property string pendingPower: ""
    onVisibleChanged: if (!visible) pendingPower = ""
    spacing: 12
    Text { text: "Яркость"; color: control.shell.colors.fg; font.pixelSize: 14 }
    RowLayout {
        Layout.fillWidth: true
        Text { text: "󰃠"; color: control.shell.colors.fg; font.pixelSize: 20 }
        ThemedSlider {
        shell: control.shell; Layout.fillWidth: true; from: 5; to: 100; value: Math.max(5, control.systemState.brightness || 5); enabled: !!control.systemState.available && control.systemState.brightness >= 0; onMoved: control.shell.send("brightness", {value: Math.round(value)}) }
        Text { text: (control.systemState.brightness >= 0 ? control.systemState.brightness : "—") + "%"; color: control.shell.colors.fg }
    }
    Text { visible: control.systemState.brightness < 0; text: "Управление яркостью недоступно"; color: control.shell.colors.fg_dim; font.pixelSize: 11 }
}
