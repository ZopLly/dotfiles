pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris
ShellRoot {
    id: root
    property var state: ({workspaces: [], widgets: {}, vpns: [], profiles: [], preview: true, volume: -1})
    property var colors: state.colors ? Object.assign({}, state.colors, {bg_modules: state.colors.shell_bg_modules || state.colors.bg_modules}) : ({bg: "#1e1e2e", fg: "#cdd6f4", fg_dim: "#6c7086", bg_modules: "#11111b", accent: "#89b4fa", power_color: "#f38ba8"})
    property date now: new Date()
    property string openPanel: ""
    property string editorPanel: ""
    property string openScreen: ""
    property bool editMode: false
    property bool snapToGrid: state.widgets && state.widgets._options ? state.widgets._options.snap : true
    property string errorMessage: ""
    property int playerIndex: -1
    property var players: Mpris.players.values
    property var player: players.length ? (playerIndex >= 0 ? players[Math.min(playerIndex, players.length-1)] : (players.find(p => p.isPlaying) || players[0])) : null
    property var panelLayouts: ({center: ["calendar", "media"], right: ["connectivity", "vpn", "audio", "brightness", "power", "desktop"]})
    property var calendarLive: ({configured: false, events: []})
    property var calendarState: state.preview ? ({configured: true, preview: true, events: [
        {date: Qt.formatDate(now, "yyyy-MM-dd"), time: "10:00", title: "Пример: встреча", allDay: false},
        {date: Qt.formatDate(now, "yyyy-MM-dd"), title: "Пример: заметка на день", allDay: true}
    ]}) : calendarLive
    property var weather: ({})
    property var moduleCatalog: [
        {id: "weather", label: "Погода"},
        {id: "calendar", label: "Календарь"}, {id: "media", label: "Плеер"},
        {id: "connectivity", label: "Подключения"}, {id: "vpn", label: "VPN"},
        {id: "audio", label: "Звук"}, {id: "brightness", label: "Яркость"},
        {id: "power", label: "Питание"}, {id: "desktop", label: "Виджеты рабочего стола"}
    ]
    function panelModules(panel) { return panelLayouts[panel] || (panel === "center" ? ["calendar", "media"] : ["connectivity", "vpn", "audio", "brightness", "power", "desktop"]) }
    function workspace(output) { return (state.workspaces || []).find(w => w.output === output && w.is_active) || {idx: 1} }
    function workspaceKey(output) { let w = workspace(output); return w.name ? "name:"+w.name : "index:"+w.idx }
    function widgetConfig(output, id) { return (((state.widgets || {})[output] || {}).workspaces || {})[workspaceKey(output)]?.[id] || {} }
    function widgetVisible(output, id) { let config = widgetConfig(output, id); return config.visible === undefined ? (id !== "weather" && workspace(output).idx === 1) : config.visible }
    function send(action, args) { backend.write(JSON.stringify({action: action, args: args || {}})+"\n") }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }
    Timer { id: errorTimer; interval: 7000; onTriggered: root.errorMessage = "" }
    Process {
        id: backend
        command: ["python3", Quickshell.shellDir+"/backend.py"]
        running: true
        stdinEnabled: true
        stdout: SplitParser {
            onRead: data => {
                try {
                    let event = JSON.parse(data)
                    if (event.type === "state") {
                        if (event.data.panels && JSON.stringify(root.panelLayouts) !== JSON.stringify(event.data.panels))
                            root.panelLayouts = event.data.panels
                        root.state = event.data
                    }
                    else { root.errorMessage = event.message; errorTimer.restart() }
                } catch(e) { console.warn("Backend response:", e) }
            }
        }
        onExited: { root.errorMessage = "Служба панели остановилась. Перезапусти оболочку." }
    }
    Process {
        command: ["python3", Quickshell.shellDir+"/weather.py"]
        running: true
        stdout: SplitParser { onRead: data => { try { root.weather = JSON.parse(data) } catch(e) { console.warn("Invalid weather response") } } }
    }
    Process {
        command: ["bash", Quickshell.shellDir+"/calendar-service.sh"]
        running: true
        stdout: SplitParser { onRead: data => { try { root.calendarLive = JSON.parse(data) } catch(e) { console.warn("Invalid calendar response") } } }
    }
    IpcHandler {
        target: "shell"
        function panel(name: string): void {
            root.openScreen = Quickshell.screens[0].name
            root.openPanel = name === "center" || name === "right" ? name : ""
        }
        function customize(name: string): void {
            if (name !== "center" && name !== "right" && name !== "") return
            root.editorPanel = name
            if (name !== "") { root.openScreen = Quickshell.screens[0].name; root.openPanel = name }
        }
        function modules(panel: string, values: string): void {
            try { root.send("save-panel", {panel: panel, modules: values === "-" ? [] : values.split(",")}) }
            catch(e) { root.errorMessage = "Invalid module list"; errorTimer.restart() }
        }
        function edit(): void { root.openScreen = Quickshell.screens[0].name; root.editMode = !root.editMode }
        function status(): string { return JSON.stringify({panel: root.openPanel, edit: root.editMode, title: root.player ? root.player.trackTitle : "", playing: root.player ? root.player.isPlaying : false, widgets: root.state.widgets || {}, panels: root.state.panels || {}}) }
        function media(action: string): void {
            if (!root.player) return
            if (action === "toggle" && root.player.canTogglePlaying) root.player.togglePlaying()
            if (action === "next" && root.player.canGoNext) root.player.next()
            if (action === "previous" && root.player.canGoPrevious) root.player.previous()
        }
    }
    Variants {
        model: Quickshell.screens
        delegate: Bar { required property var modelData; screen: modelData; shell: root }
    }
    Variants {
        model: Quickshell.screens
        delegate: Desktop { required property var modelData; screen: modelData; shell: root }
    }
}
