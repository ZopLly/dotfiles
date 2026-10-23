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
    Text { text: "Виджеты · пространство " + (control.shell.workspace(control.outputName).name || control.shell.workspace(control.outputName).idx); color: control.shell.colors.fg; font.pixelSize: 14 }
    Flow {
        Layout.fillWidth: true
        spacing: 8
        Repeater {
            model: [{id: "clock", label: "Часы"}, {id: "media", label: "Плеер"}, {id: "weather", label: "Погода"}, {id: "metrics", label: "Нагрузка"}]
            ActionButton {
                required property var modelData
                shell: control.shell
                text: modelData.label
                selected: control.shell.widgetVisible(control.outputName, modelData.id)
                onClicked: control.shell.send("save-widget", {output: control.outputName, workspace: control.shell.workspaceKey(control.outputName), id: modelData.id, visible: !selected})
            }
        }
    }
    ActionButton { shell: control.shell; Layout.fillWidth: true; text: control.shell.editMode ? "Готово: виджеты закреплены" : "Расположение виджетов"; selected: control.shell.editMode; onClicked: { control.shell.editMode = !control.shell.editMode; control.shell.openPanel = "" } }
    ActionButton { shell: control.shell; Layout.fillWidth: true; text: control.shell.snapToGrid ? "Привязка к сетке: включена" : "Привязка к сетке: выключена"; onClicked: control.shell.send("grid", {enabled: !control.shell.snapToGrid}) }

}
