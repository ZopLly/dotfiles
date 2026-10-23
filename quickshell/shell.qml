pragma ComponentBehavior: Bound
import QtQuick
import "StateMerge.js" as StateMerge
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris
ShellRoot {
    id: root
    property var dashboard: dashboardController
    DashboardController { id: dashboardController; shell: root }
    property var notifications: notificationsController
    NotificationsController { id: notificationsController }
    property var applications: applicationsController
    ApplicationsController { id: applicationsController; shell: root }
    property var state: ({workspaces: [], widgets: {}, vpns: [], profiles: [], preview: true, volume: -1})
    property var workspaces: state.workspaces || []
    property var widgets: state.widgets || ({})
    property var palette: state.colors || null
    property var colors: palette ? Object.assign({}, palette, {bg_modules: palette.shell_bg_modules || palette.bg_modules}) : ({bg: "#1e1e2e", fg: "#cdd6f4", fg_dim: "#6c7086", bg_modules: "#11111b", accent: "#89b4fa", power_color: "#f38ba8"})
    property date now: new Date()
    signal controlPageRequested(string page)
    property string openPanel: ""
    property string editorPanel: ""
    property string openScreen: ""
    property bool editMode: false
    property bool snapToGrid: state.widgets && state.widgets._options ? state.widgets._options.snap : true
    property string osdKind: ""
    property string osdScreen: workspaces.find(w => w.is_focused)?.output || (Quickshell.screens.length ? Quickshell.screens[0].name : "")
    property var pendingControls: ({})
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
    function workspace(output) { return workspaces.find(w => w.output === output && w.is_active) || {idx: 1} }
    function workspaceKey(output) { let w = workspace(output); return w.name ? "name:"+w.name : "index:"+w.idx }
    function widgetConfig(output, id) { return ((widgets[output] || {}).workspaces || {})[workspaceKey(output)]?.[id] || {} }
    function widgetVisible(output, id) { let config = widgetConfig(output, id); return config.visible === undefined ? (["clock", "media"].includes(id) && workspace(output).idx === 1) : config.visible }
    function setProfile(value) { send("profile", {value: value}) }
    function send(action, args) {
        if (action === "launcher") { applications.toggle("launcher",osdScreen);return }
        if (["volume", "mic-volume", "brightness"].includes(action)) {
            pendingControls[action] = args
            if (!controlTimer.running) controlTimer.start()
        } else backend.write(JSON.stringify({action: action, args: args || {}})+"\n")
    }
    Timer {
        id: controlTimer; interval: 100
        onTriggered: {
            let controls = root.pendingControls
            root.pendingControls = ({})
            for (let action in controls) backend.write(JSON.stringify({action: action, args: controls[action]})+"\n")
        }
    }
    Timer { id: osdTimer; interval: 1800; onTriggered: root.osdKind = "" }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: {
        let current = new Date()
        if (Math.floor(current.getTime()/60000) !== Math.floor(root.now.getTime()/60000)) root.now = current
    } }
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
                        root.state = StateMerge.retainEqual(root.state, event.data)
                    }
                    else if (event.type === "osd") { root.osdKind = event.data.kind; osdTimer.restart() }
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
            root.openPanel = ["center", "right", "notifications"].includes(name) ? name : ""
        }
        function profile(value: string): void { root.setProfile(value) }
        function page(name: string): void {
            if (!["main", "wifi", "bluetooth", "audio", "vpn", "desktop"].includes(name)) return
            root.openScreen = Quickshell.screens[0].name
            root.openPanel = "right"
            root.controlPageRequested(name)
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
        function systemStatus(): string {
            let s = root.state
            return JSON.stringify({revision: s.revision || "", preview: s.preview, error: root.errorMessage,
                volume: s.volume, muted: s.muted, micVolume: s.mic_volume, micMuted: s.mic_muted,
                brightness: s.brightness, wifi: s.wifi, wifiConnected: s.wifi_connected,
                wifiSignal: s.wifi_signal, ssidPresent: !!s.wifi_connected && !!s.network,
                networkCount: (s.networks || []).length, bluetooth: s.bluetooth,
                bluetoothAvailable: s.bluetooth_available, bluetoothConnected: (s.bluetooth_devices || []).filter(d => d.connected).length,
                sinkCount: (s.sinks || []).length, sourceCount: (s.sources || []).length,
                profile: s.profile, battery: s.battery, surface: root.colors.bg_modules})
        }
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
        delegate: Osd { required property var modelData; screen: modelData; outputName: modelData.name; shell: root }
    }
    Variants {
        model: Quickshell.screens
        delegate: Desktop { required property var modelData; screen: modelData; shell: root }
    }
}
