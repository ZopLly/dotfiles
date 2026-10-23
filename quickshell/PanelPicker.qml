pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: picker
    required property var shell
    required property string panel
    property var selectedModules: shell.panelModules(panel)
    function update(values) { shell.send("save-panel", {panel: panel, modules: values}) }
    function move(index, delta) {
        let values = selectedModules.slice()
        let item = values.splice(index, 1)[0]
        values.splice(index+delta, 0, item)
        update(values)
    }
    spacing: 8
    Text { text: "Модули панели"; font.pixelSize: 18; color: picker.shell.colors.fg }
    Text { text: "Порядок сверху вниз · сохраняется автоматически"; wrapMode: Text.Wrap; Layout.fillWidth: true; font.pixelSize: 11; color: picker.shell.colors.fg_dim }
    Repeater {
        model: picker.selectedModules
        RowLayout {
            required property string modelData
            required property int index
            id: entry
            Layout.fillWidth: true
            Text { text: (picker.shell.moduleCatalog.find(m => m.id === entry.modelData) || {}).label || entry.modelData; Layout.fillWidth: true; elide: Text.ElideRight; color: picker.shell.colors.fg; font.pixelSize: 12 }
            ActionButton { shell: picker.shell; text: "↑"; enabled: entry.index > 0; onClicked: picker.move(entry.index, -1) }
            ActionButton { shell: picker.shell; text: "↓"; enabled: entry.index < picker.selectedModules.length-1; onClicked: picker.move(entry.index, 1) }
            ActionButton { shell: picker.shell; text: "−"; onClicked: picker.update(picker.selectedModules.filter(m => m !== entry.modelData)) }
        }
    }
    Text { text: "Добавить"; color: picker.shell.colors.fg; font.pixelSize: 14 }
    Repeater {
        model: picker.shell.moduleCatalog.filter(m => !picker.selectedModules.includes(m.id))
        ActionButton {
            required property var modelData
            shell: picker.shell; Layout.fillWidth: true
            text: "+ " + modelData.label
            onClicked: picker.update(picker.selectedModules.concat([modelData.id]))
        }
    }
    ActionButton { shell: picker.shell; Layout.fillWidth: true; text: "Вернуть стандартный набор"; onClicked: picker.update(picker.panel === "center" ? ["calendar", "media"] : ["connectivity", "vpn", "audio", "brightness", "power", "desktop"]) }
}
