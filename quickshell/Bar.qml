pragma ComponentBehavior: Bound
import QtQuick
import "StatusIcons.js" as Icons
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Services.SystemTray
PanelWindow {
    id: bar
    required property var shell
    property bool expanded: shell.openScreen === screen.name && shell.openPanel !== ""
    property bool centerOpen: expanded && shell.openPanel === "center"
    property bool rightOpen: expanded && shell.openPanel === "right"
    anchors { top: true; left: true; right: true }
    implicitHeight: expanded || shell.applications.error !== "" || centerIsland.height > 41 || rightIsland.height > 41 ? screen.height : 56
    exclusiveZone: 56
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "niri-shell-bar"
    WlrLayershell.keyboardFocus: expanded || (shell.editMode && shell.openScreen === screen.name) ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    mask: Region {
        width: bar.expanded ? bar.width : 0
        height: bar.expanded ? bar.height : 0
        Region { item: leftIsland }
        Region { item: appErrorBanner }
        Region { item: centerIsland }
        Region { item: rightIsland }
    }
    Connections {
        target: bar.shell
        function onEditorPanelChanged() { centerScroll.contentY = 0; rightScroll.contentY = 0 }
        function onOpenPanelChanged() { centerScroll.contentY = 0; rightScroll.contentY = 0 }
        function onControlPageRequested(page) { if (bar.shell.openScreen === bar.screen.name) controlCenter.navigate(page) }
    }
    Connections { target: controlCenter; function onPageChanged() { rightScroll.contentY = 0 } }
    function toggle(panel) {
        let closing = shell.openScreen === screen.name && shell.openPanel === panel
        shell.openScreen = screen.name
        shell.openPanel = closing ? "" : panel
    }
    Item {
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: { bar.shell.openPanel = ""; bar.shell.editMode = false }
        MouseArea { anchors.fill: parent; enabled: bar.expanded; onClicked: bar.shell.openPanel = "" }
        WorkspaceIsland {
            id: leftIsland
            x: 12; y: 8
            maxWidth: Math.max(120,bar.width/2-(bar.width < 500 ? 35 : bar.width < 700 ? 70 : 98)-24)
            shell: bar.shell; outputName: bar.screen.name
        }
        Rectangle {
            id: centerIsland
            x: (bar.width-width)/2; y: 8
            width: bar.centerOpen ? Math.min(840, bar.width-24) : (bar.width < 500 ? 70 : bar.width < 700 ? 140 : 196)
            height: bar.centerOpen ? Math.min(bar.screen.height-24, centerContent.implicitHeight+64) : 40
            radius: 22; color: bar.shell.colors.bg_modules; clip: true
            MouseArea { anchors.fill: parent; onClicked: function(mouse) { mouse.accepted = true } }
            Behavior on width { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
            Behavior on height { NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }
            ActionButton { shell: bar.shell; width: parent.width; height: 40; quiet: true; text: bar.shell.editMode ? "Готово: закрепить виджеты" : (bar.width < 500 ? Qt.formatTime(bar.shell.now, "HH:mm") : bar.shell.now.toLocaleString(Qt.locale("ru_RU"), bar.width < 700 ? "d MMM HH:mm" : "ddd d MMM · HH:mm")); onClicked: { if (bar.shell.editMode) bar.shell.editMode = false; else bar.toggle("center") } }
            Flickable {
                id: centerScroll
                flickableDirection: Flickable.VerticalFlick
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: parent.contentHeight > parent.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }
                anchors { top: parent.top; topMargin: 48; bottom: parent.bottom; bottomMargin: 16; left: parent.left; right: parent.right; margins: 16 }
                clip: true
                opacity: bar.centerOpen ? 1 : 0
                visible: opacity > 0
                Behavior on opacity { NumberAnimation { duration: 180 } }
                contentWidth: width
                contentHeight: centerContent.implicitHeight
                onContentHeightChanged: contentY = Math.max(0, Math.min(contentY, contentHeight-height))
                ColumnLayout {
                    id: centerContent
                    width: parent.width
                    height: implicitHeight
                    spacing: 14
                    Dashboard { shell: bar.shell; outputName: bar.screen.name; Layout.fillWidth: true }
                }
            }
        }
        Rectangle {
            id: rightIsland
            x: bar.width-width-12; y: 8
            width: bar.rightOpen ? Math.min(390, bar.width-24) : Math.min(statusRow.implicitWidth+16, Math.max(100, bar.width/2-115))
            height: bar.rightOpen ? Math.min(bar.screen.height-24, controlContent.implicitHeight+64) : 40
            radius: 22; color: bar.shell.colors.bg_modules; clip: true
            MouseArea { anchors.fill: parent; onClicked: function(mouse) { mouse.accepted = true } }
            Behavior on width { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
            Behavior on height { NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }
            RowLayout {
                id: statusRow
                anchors.right: parent.right; anchors.rightMargin: 8
                anchors.top: parent.top
                width: Math.min(implicitWidth, parent.width-16)
                height: 40; spacing: 2
                ActionButton {
                    shell: bar.shell; Layout.preferredWidth: 40; Layout.minimumWidth: 40
                    height: 40; quiet: true
                    text: bar.shell.notifications.state.dnd ? "󰂛" : "󰂚"
                    ToolTip.visible: hovered
                    ToolTip.text: "Уведомления · " + bar.shell.notifications.state.active.length
                    onClicked: { bar.shell.notifications.act("refresh",null); bar.toggle("notifications") }
                    Rectangle {
                        visible: bar.shell.notifications.state.active.length > 0
                        anchors { right: parent.right; top: parent.top; margins: 6 }
                        width: 6; height: 6; radius: 3; color: bar.shell.colors.accent
                    }
                }
                ActionButton {
                    shell: bar.shell; Layout.preferredWidth: 40; Layout.minimumWidth: 40; Layout.alignment: Qt.AlignVCenter
                    height: 40; quiet: true
                    text: (bar.shell.state.language || "").toLowerCase().includes("russian") ? "ru" : "en"
                    onClicked: bar.shell.send("layout")
                }
                ActionButton {
                    shell: bar.shell; Layout.fillWidth: true; Layout.minimumWidth: 40; Layout.alignment: Qt.AlignVCenter
                    height: 40; quiet: true
                    text: Icons.wifi(bar.shell.state) + "  " + (bar.shell.state.bluetooth_available ? Icons.bluetooth(bar.shell.state) + "  " : "") + Icons.volume(bar.shell.state.volume, bar.shell.state.muted) + " " + (bar.width >= 900 && bar.shell.state.volume >= 0 ? bar.shell.state.volume+"%  " : "") + Icons.battery(bar.shell.state.battery) + " " + (bar.shell.state.battery && bar.shell.state.battery.percent >= 0 ? Math.round(bar.shell.state.battery.percent)+" %" : "")
                    ToolTip.visible: hovered
                    ToolTip.text: [bar.shell.state.network || "Нет подключения", (bar.shell.state.battery || {}).remaining_text || ""].filter(Boolean).join("\n")
                    onClicked: bar.toggle("right")
                }
            }
            Flickable {
                id: rightScroll
                flickableDirection: Flickable.VerticalFlick
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: parent.contentHeight > parent.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }
                anchors { top: parent.top; topMargin: 48; bottom: parent.bottom; bottomMargin: 16; left: parent.left; right: parent.right; margins: 16 }
                clip: true; contentWidth: width
                contentHeight: controlContent.implicitHeight
                onContentHeightChanged: contentY = Math.max(0, Math.min(contentY, contentHeight-height))
                opacity: bar.rightOpen ? 1 : 0
                visible: opacity>0
                Behavior on opacity { NumberAnimation { duration: 180 } }
                ColumnLayout {
                    id: controlContent
                    width: parent.width
                    height: implicitHeight
                    RowLayout {
                        visible: SystemTray.items.values.length > 0
                        Repeater {
                            model: SystemTray.items
                            Item {
                                required property var modelData
                                implicitWidth: 32; implicitHeight: 32
                                Image { anchors.fill: parent; anchors.margins: 5; source: parent.modelData.icon }
                                MouseArea {
                                    anchors.fill: parent
                                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                                    onClicked: function(mouse) {
                                        if (mouse.button === Qt.RightButton || parent.modelData.onlyMenu) {
                                            let pos = mapToItem(bar.contentItem, mouse.x, mouse.y)
                                            parent.modelData.display(bar, Math.round(pos.x), Math.round(pos.y))
                                        } else parent.modelData.activate()
                                    }
                                }
                            }
                        }
                    }
                    ControlCard { id: controlCenter; shell: bar.shell; outputName: bar.screen.name; Layout.fillWidth: true }
                }
            }
        }
        NotificationsDrawer {
            visible: bar.expanded && bar.shell.openPanel === "notifications"
            x: bar.width-width-12; y: 58; width: Math.min(440,bar.width-24)
            height: Math.min(implicitHeight,bar.screen.height-80)
            shell: bar.shell
        }
        ApplicationsDrawer {
            visible: bar.expanded && (bar.shell.openPanel === "launcher" || bar.shell.openPanel === "applications")
            x: 12; y: 58; width: Math.min(600,bar.width-24); height: Math.min(implicitHeight,bar.screen.height-80)
            shell: bar.shell; outputName: bar.screen.name
        }
        Rectangle {
            id: appErrorBanner
            visible: bar.shell.applications.error !== ""
            z: 3
            anchors { top: parent.top; topMargin: 62; horizontalCenter: parent.horizontalCenter }
            width: Math.min(480,bar.width-32); height: appError.implicitHeight+24
            radius: 12; color: bar.shell.colors.bg
            Text { id: appError; anchors.fill: parent; anchors.margins: 12; text: bar.shell.applications.error; color: bar.shell.colors.power_color; wrapMode: Text.Wrap; font.pixelSize: 12 }
            TapHandler { onTapped: bar.shell.applications.error = "" }
        }
        Rectangle {
            visible: bar.shell.errorMessage !== ""
            anchors { top: parent.top; topMargin: 62; horizontalCenter: parent.horizontalCenter }
            width: Math.min(480, bar.width-32); height: message.implicitHeight+24
            radius: 12; color: bar.shell.colors.bg
            Text { id: message; anchors.fill: parent; anchors.margins: 12; text: bar.shell.errorMessage; color: bar.shell.colors.power_color; wrapMode: Text.Wrap; font.pixelSize: 12 }
        }
    }
}
