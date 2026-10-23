pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Quickshell
import Quickshell.Io

ShellRoot {
    id: app
    property var state: ({themes: [], wallpapers: [], selection: {}, preview: false, state_error: false, can_restore: false, wallpaper_status: "confirmed"})
    property var thumbnails: ({})
    property bool busy: false
    property string error: ""
    property string pageName: "colors"
    property var colors: state.colors || ({})
    property color bg: colors.bg || "#17283a"
    property color fg: colors.fg || "#f3e7d0"
    property color surface: colors.surface && colors.surface !== colors.bg ? colors.surface : Qt.tint(bg, Qt.rgba(fg.r,fg.g,fg.b,0.07))
    property color accent: colors.accent || "#81b5d5"
    property var chosenTheme: (state.themes || []).find(t => t.id === state.selection.palette_id) || null

    function choose(fields) {
        if (busy || !(state.enabled ?? state.preview)) return
        busy = true; error = ""
        backend.write(JSON.stringify({action: "select", fields: fields})+"\n")
    }
    function operate(action) {
        if (busy || !(state.enabled ?? state.preview)) return
        busy = true; error = ""
        backend.write(JSON.stringify({action: action})+"\n")
    }
    function thumbnail(id) { backend.write(JSON.stringify({action: "thumbnail", id: id})+"\n") }
    function contrast(c) {
        let linear = v => v <= 0.04045 ? v/12.92 : Math.pow((v+0.055)/1.055,2.4)
        return 0.2126*linear(c.r)+0.7152*linear(c.g)+0.0722*linear(c.b)>0.179 ? "#101820" : "#ffffff"
    }
    Process {
        id: backend
        command: ["python3", Quickshell.shellDir+"/../appearance/bridge.py"]
        stdinEnabled: true; running: true
        stdout: SplitParser {
            onRead: data => {
                try {
                    let event = JSON.parse(data)
                    if (event.type === "state") {
                        app.state = event.data; app.error = event.data.error || ""; app.busy = false
                    } else if (event.type === "thumbnail") {
                        let copy = Object.assign({}, app.thumbnails)
                        copy[event.id] = event.url; app.thumbnails = copy
                    } else { app.error = event.message || "Ошибка оформления"; app.busy = false }
                } catch(e) { app.error = "Не удалось прочитать ответ настроек"; app.busy = false }
            }
        }
        onExited: { app.busy = false; app.error = "Служба оформления остановилась" }
    }
    IpcHandler {
        target: "appearance"
        function show(): void { window.visible = true; window.requestActivate() }
        function status(): string { return JSON.stringify({selection: app.state.selection, themes: app.state.themes.length, wallpapers: app.state.wallpapers.length, busy: app.busy, error: app.error, page: app.pageName}) }
        function choosePalette(id: string, mode: string, accent: string): void { app.choose({palette_id: id, mode: mode === "-" ? null : mode, accent_id: accent === "-" ? null : accent}) }
        function chooseWallpaper(id: string): void { app.choose({wallpaper_id: id}) }
        function page(name: string): void { if (name === "colors" || name === "wallpapers") app.pageName = name }
    }
    ApplicationWindow {
        id: window
        visible: true
        title: "Настройки Niri · Оформление"
        width: Math.min(1160, Screen.width-48); height: Math.min(820, Screen.height-48)
        minimumWidth: 620; minimumHeight: 400
        color: app.bg
        font.pixelSize: 14
        palette.window: app.bg
        palette.windowText: app.fg
        palette.text: app.fg
        palette.base: app.bg
        palette.button: app.surface
        palette.buttonText: app.fg
        palette.highlight: app.accent
        palette.highlightedText: app.contrast(app.accent)
        onClosing: event => { event.accepted = false; window.visible = false }
        Shortcut { sequence: "Escape"; onActivated: window.visible = false }
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 22; spacing: 14
            RowLayout {
                Layout.fillWidth: true
                Label { text: "Настройки"; font.pixelSize: 26; font.bold: true; Layout.fillWidth: true }
                BusyIndicator { running: app.busy; visible: running; Layout.preferredWidth: 30; Layout.preferredHeight: 30 }
                AppearanceButton { text: "Закрыть"; onClicked: window.visible = false }
            }
            Rectangle {
                Layout.fillWidth: true; implicitHeight: notice.implicitHeight+20
                radius: 12; color: app.surface
                Label {
                    id: notice; anchors.fill: parent; anchors.margins: 10
                    text: app.state.preview ? "Предпросмотр · выбор меняет только тестовую копию рабочего стола" : (app.state.enabled ? "Настройки оформления Niri" : "Просмотр оформления · применение недоступно")
                    wrapMode: Text.WordWrap
                }
            }
            Label { visible: app.error !== ""; text: app.error; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: app.fg }
            RowLayout {
                visible: app.state.wallpaper_status === "unconfirmed" || (app.state.state_error && app.state.can_restore)
                AppearanceButton { visible: app.state.wallpaper_status === "unconfirmed"; text: "Проверить фон"; enabled: !app.busy; onClicked: app.operate("confirm-wallpaper") }
                AppearanceButton { visible: app.state.state_error && app.state.can_restore; text: "Восстановить копию"; enabled: !app.busy; onClicked: app.operate("restore") }
            }
            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 20
                Rectangle {
                    color: app.surface; radius: 14; Layout.preferredWidth: 150; Layout.fillHeight: true
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 12
                        Label { text: "РАЗДЕЛЫ"; font.pixelSize: 11; opacity: 0.7 }
                        AppearanceButton { text: "Оформление"; highlighted: true; Layout.fillWidth: true; onClicked: {} }
                        Item { Layout.fillHeight: true }
                        Label { text: "Niri"; font.pixelSize: 18; font.bold: true }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
                    RowLayout {
                        AppearanceButton { text: "Цвета"; checkable: true; checked: app.pageName === "colors"; onClicked: app.pageName = "colors" }
                        AppearanceButton { text: "Обои"; checkable: true; checked: app.pageName === "wallpapers"; onClicked: app.pageName = "wallpapers" }
                        Item { Layout.fillWidth: true }
                    }
                    RowLayout {
                        visible: app.pageName === "colors" && app.chosenTheme !== null && app.chosenTheme.group === "hyprstack"
                        Layout.fillWidth: true
                        ComboBox {
                            padding: 12; font.pixelSize: 14
                            id: modes
                            model: ["Тёмный", "Светлый"]
                            currentIndex: app.state.selection.mode === "light" ? 1 : 0
                            enabled: !app.busy
                            onActivated: app.choose({mode: currentIndex === 1 ? "light" : "dark"})
                        }
                        ComboBox {
                            padding: 12; font.pixelSize: 14
                            id: accents
                            property var options: [{id: "", label: "Исходный акцент"}].concat(app.chosenTheme ? app.chosenTheme.accents : [])
                            model: options; textRole: "label"
                            currentIndex: Math.max(0, options.findIndex(a => a.id === (app.state.selection.accent_id || "")))
                            Layout.fillWidth: true; enabled: !app.busy
                            onActivated: app.choose({accent_id: options[currentIndex].id || null})
                        }
                    }
                    ThemeGrid { visible: app.pageName === "colors"; appRoot: app; Layout.fillWidth: true; Layout.fillHeight: true }
                    WallpaperGrid { visible: app.pageName === "wallpapers"; appRoot: app; Layout.fillWidth: true; Layout.fillHeight: true }
                }
            }
        }
    }
}
