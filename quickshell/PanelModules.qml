pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: modules
    required property var shell
    required property string outputName
    required property string panel
    property var navigator: null
    property bool editing: shell.editorPanel === panel
    spacing: 12
    ActionButton {
        shell: modules.shell; Layout.fillWidth: true
        text: modules.editing ? "Готово" : "Настроить модули"
        selected: modules.editing
        onClicked: modules.shell.editorPanel = modules.editing ? "" : modules.panel
    }
    Loader {
        Layout.fillWidth: true
        visible: active
        Layout.preferredHeight: item ? item.implicitHeight : 0
        Layout.fillHeight: false
        active: modules.editing
        sourceComponent: Component { PanelPicker { shell: modules.shell; panel: modules.panel } }
    }
    Text {
        visible: modules.shell.panelModules(modules.panel).length === 0 && !modules.editing
        text: "Панель пуста. Добавь модули в настройках."
        color: modules.shell.colors.fg_dim; wrapMode: Text.Wrap; Layout.fillWidth: true
    }
    Repeater {
        model: modules.editing ? [] : modules.shell.panelModules(modules.panel)
        Loader {
            id: moduleLoader
            required property string modelData
            Layout.fillWidth: true
            Layout.preferredHeight: item ? item.implicitHeight : 0
            Layout.fillHeight: false
            sourceComponent: modules.navigator && (modelData === "vpn" || modelData === "desktop") ? shortcut : modelData === "weather" ? forecast : modelData === "calendar" ? calendar : modelData === "media" ? media : modelData === "connectivity" ? connectivity : modelData === "vpn" ? vpn : modelData === "audio" ? audio : modelData === "brightness" ? brightness : modelData === "power" ? power : desktop
            Component { id: shortcut; ActionButton { shell: modules.shell; text: moduleLoader.modelData === "vpn" ? "VPN ›" : "Виджеты рабочего стола ›"; onClicked: modules.navigator.navigate(moduleLoader.modelData) } }
            Component { id: forecast; WeatherCard { shell: modules.shell } }
            Component { id: calendar; CalendarCard { shell: modules.shell } }
            Component { id: media; MediaCard { shell: modules.shell } }
            Component { id: connectivity; ConnectivityModule { shell: modules.shell; outputName: modules.outputName; navigator: modules.navigator } }
            Component { id: vpn; VpnModule { shell: modules.shell; outputName: modules.outputName } }
            Component { id: audio; AudioModule { shell: modules.shell; outputName: modules.outputName; navigator: modules.navigator; detailed: !modules.navigator } }
            Component { id: brightness; BrightnessModule { shell: modules.shell; outputName: modules.outputName } }
            Component { id: power; PowerModule { shell: modules.shell; outputName: modules.outputName } }
            Component { id: desktop; DesktopControlsModule { shell: modules.shell; outputName: modules.outputName } }
        }
    }
}
