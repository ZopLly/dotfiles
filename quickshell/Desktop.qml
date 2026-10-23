pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
PanelWindow {
    id: desktop
    required property var shell
    property string workspaceKey: shell.workspaceKey(screen.name)
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Bottom
    WlrLayershell.namespace: "niri-shell-desktop"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: Region {
        x: clockWidget.x; y: clockWidget.y
        width: clockWidget.visible ? clockWidget.width : 0
        height: clockWidget.visible ? clockWidget.height : 0
        Region { x: weatherWidget.x; y: weatherWidget.y; width: weatherWidget.visible ? weatherWidget.width : 0; height: weatherWidget.visible ? weatherWidget.height : 0 }
        Region { x: metricsWidget.x; y: metricsWidget.y; width: metricsWidget.visible ? metricsWidget.width : 0; height: metricsWidget.visible ? metricsWidget.height : 0 }
        Region { x: mediaWidget.x; y: mediaWidget.y; width: mediaWidget.visible ? mediaWidget.width : 0; height: mediaWidget.visible ? mediaWidget.height : 0 }
    }
    component DesktopTile: WidgetFrame {
        shell: desktop.shell
        editing: desktop.shell.editMode
        id: tile
        required property string widgetId
        property var stored: desktop.shell.widgetConfig(desktop.screen.name, widgetId)
        property bool manipulating: moveArea.pressed || resizeArea.pressed
        visible: desktop.shell.widgetVisible(desktop.screen.name, widgetId)
        function restore() {
            if (manipulating) return
            width = Math.min(desktop.width, stored.width || 320)
            height = Math.min(Math.max(1, desktop.height-64), stored.height || 180)
            x = Math.max(0, Math.min(desktop.width-width, (stored.x === undefined ? (["weather", "metrics"].includes(widgetId) ? 0.65 : 0.08) : stored.x)*(desktop.width-width)))
            y = Math.max(64, Math.min(desktop.height-height, (stored.y === undefined ? (widgetId === "clock" ? 0.22 : widgetId === "metrics" ? 0.78 : 0.55) : stored.y)*(desktop.height-height)))
        }
        Component.onCompleted: restore()
        onStoredChanged: restore()
        Connections {
            target: desktop
            function onWorkspaceKeyChanged() { Qt.callLater(tile.restore) }
            function onWidthChanged() { tile.restore() }
            function onHeightChanged() { tile.restore() }
        }
        function persist() {
            if (desktop.shell.snapToGrid) { x=Math.round(x/16)*16; y=Math.round(y/16)*16 }
            x = Math.max(0, Math.min(desktop.width-width, x))
            y = Math.max(64, Math.min(desktop.height-height, y))
            desktop.shell.send("save-widget", {output: desktop.screen.name, workspace: desktop.workspaceKey, id: widgetId, x: x/Math.max(1, desktop.width-width), y: y/Math.max(1, desktop.height-height), width: Math.round(width), height: Math.round(height)})
        }
        MouseArea {
            id: moveArea
            anchors.fill: parent
            enabled: desktop.shell.editMode
            z: 10
            cursorShape: Qt.SizeAllCursor
            drag.target: tile
            drag.minimumX: 0; drag.maximumX: Math.max(0, desktop.width-tile.width)
            drag.minimumY: 64; drag.maximumY: Math.max(64, desktop.height-tile.height)
            onReleased: tile.persist()
        }
        Rectangle {
            visible: desktop.shell.editMode
            width: 26; height: 26; radius: 8
            color: desktop.shell.colors.accent
            anchors { right: parent.right; bottom: parent.bottom; margins: 6 }
            z: 11
            Text { anchors.centerIn: parent; text: "◢"; color: desktop.shell.colors.bg }
            MouseArea {
                id: resizeArea
                anchors.fill: parent
                cursorShape: Qt.SizeFDiagCursor
                property point start
                property real oldWidth
                property real oldHeight
                onPressed: function(mouse) { start = mapToItem(desktop.contentItem, mouse.x, mouse.y); oldWidth=tile.width; oldHeight=tile.height }
                onPositionChanged: function(mouse) {
                    if (!pressed) return
                    let point=mapToItem(desktop.contentItem, mouse.x, mouse.y)
                    tile.width=Math.max(220, Math.min(520, desktop.width-tile.x, oldWidth+point.x-start.x))
                    tile.height=Math.max(150, Math.min(420, desktop.height-tile.y, oldHeight+point.y-start.y))
                }
                onReleased: tile.persist()
            }
        }
    }
    DesktopTile {
        id: clockWidget
        widgetId: "clock"
        DesktopClock { anchors.centerIn: parent; width: parent.width-32; shell: desktop.shell }
    }
    DesktopTile {
        id: mediaWidget
        widgetId: "media"
        MediaCard { anchors.fill: parent; anchors.margins: 18; shell: desktop.shell; compact: true }
    }
    DesktopTile {
        id: weatherWidget
        widgetId: "weather"
        clip: true
        WeatherCard { anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 16; shell: desktop.shell; compact: true }
    }
    DesktopTile {
        id: metricsWidget
        widgetId: "metrics"
        clip: true
        LoadWidget { anchors.fill: parent; anchors.margins: 18; shell: desktop.shell }
    }
}
