pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Rectangle {
    id:drawer
    required property var shell
    required property string outputName
    property bool launcher:shell.openPanel==="launcher"
    property var appGroups:shell.applications.groupsFor(outputName).filter(g => shell.applications.selectedGroup==="" || g.id===shell.applications.selectedGroup)
    color:shell.colors.bg_modules;radius:22;clip:true
    implicitHeight:launcher?570:Math.max(150,list.contentHeight+96)
    MouseArea { anchors.fill:parent;onClicked:mouse => mouse.accepted=true }
    function focusMenu() { if(launcher)menu.reset();else list.forceActiveFocus() }
    onVisibleChanged:if(visible)Qt.callLater(focusMenu)
    onLauncherChanged:if(visible)Qt.callLater(focusMenu)
    ApplicationsMenu {
        id:menu;anchors.fill:parent;anchors.margins:18
        visible:drawer.launcher;shell:drawer.shell;entries:drawer.shell.applications.entries
        onLaunch:id => drawer.shell.applications.act("launch",id)
        onSettings:drawer.shell.applications.act("settings")
    }
    ColumnLayout {
        anchors.fill:parent;anchors.margins:18;spacing:12
        visible:!drawer.launcher
        RowLayout {
            Text { text:"Открытые окна";font.pixelSize:19;font.bold:true;color:drawer.shell.colors.fg;Layout.fillWidth:true }
            ActionButton { shell:drawer.shell;text:drawer.shell.applications.currentOnly?"Этот стол":"Все столы";selected:drawer.shell.applications.currentOnly;onClicked:drawer.shell.applications.currentOnly=!drawer.shell.applications.currentOnly }
        }
        ListView {
            id:list;objectName:"windowGroups";Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:12
            model:drawer.appGroups;boundsBehavior:Flickable.StopAtBounds
            highlight:Rectangle { radius:12; color:drawer.shell.colors.accent;opacity:.18;visible:list.activeFocus }
            highlightMoveDuration:120
            keyNavigationEnabled:true
            function activateCurrent() {
                if(currentIndex>=0 && currentIndex<drawer.appGroups.length) {
                    let windows=drawer.appGroups[currentIndex].windows
                    if(windows.length)drawer.shell.applications.act("focus",windows[0].id)
                }
            }
            Keys.onReturnPressed:activateCurrent()
            Keys.onEnterPressed:activateCurrent()
            ScrollBar.vertical:ScrollBar {}
            delegate:ColumnLayout {
                id:group
                required property var modelData
                width:list.width;spacing:6
                RowLayout {
                    AppIcon { name:group.modelData.icon;label:group.modelData.name;Layout.preferredWidth:24;Layout.preferredHeight:24 }
                    Text { text:group.modelData.name;color:drawer.shell.colors.fg;font.bold:true;font.pixelSize:13;Layout.fillWidth:true;elide:Text.ElideRight }
                }
                Repeater {
                    model:group.modelData.windows
                    ColumnLayout {
                        id:windowRow
                        required property var modelData
                        Layout.fillWidth:true;spacing:2
                        Button {
                            id: focusButton
                            Keys.onReturnPressed:clicked()
                            Keys.onEnterPressed:clicked()
                            Layout.fillWidth:true;Layout.preferredHeight:42
                            text:(windowRow.modelData.is_focused?"● ":"")+windowRow.modelData.title
                            background:Rectangle {radius:10;color:drawer.shell.colors.bg}
                            contentItem:Text {text:focusButton.text;color:drawer.shell.colors.fg;elide:Text.ElideRight;verticalAlignment:Text.AlignVCenter;font.pixelSize:12}
                            onClicked:drawer.shell.applications.act("focus",windowRow.modelData.id)
                        }
                        RowLayout {
                            Text { text:"Стол "+windowRow.modelData.workspace_label;color:drawer.shell.colors.fg_dim;font.pixelSize:11;Layout.fillWidth:true }
                            ActionButton { shell:drawer.shell;text:"Полный экран";implicitHeight:32;onClicked:drawer.shell.applications.act("fullscreen",windowRow.modelData.id) }
                            ActionButton { shell:drawer.shell;text:"Развернуть";visible:windowRow.modelData.is_floating;implicitHeight:32;onClicked:drawer.shell.applications.act("maximize",windowRow.modelData.id) }
                            ActionButton { shell:drawer.shell;text:"Закрыть";implicitHeight:32;onClicked:drawer.shell.applications.act("close",windowRow.modelData.id) }
                        }
                    }
                }
            }
        }
        Text { visible:drawer.appGroups.length===0;text:"На выбранном рабочем столе нет окон";color:drawer.shell.colors.fg_dim;wrapMode:Text.Wrap;Layout.fillWidth:true }
    }
}
