pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Rectangle {
    id: drawer
    required property var shell
    property bool history: false
    property var notificationState: shell.notifications.state
    property var entries: history ? notificationState.history : notificationState.active
    implicitHeight: Math.min(620,content.implicitHeight+32)
    radius:22;color:shell.colors.bg_modules
    border.width:1;border.color:Qt.alpha(shell.colors.fg,0.12)
    MouseArea { anchors.fill:parent;onClicked:mouse => mouse.accepted=true }
    Flickable {
        anchors.fill:parent;anchors.margins:16;clip:true
        contentWidth:width;contentHeight:content.implicitHeight
        boundsBehavior:Flickable.StopAtBounds
        ScrollBar.vertical:ScrollBar {}
        ColumnLayout {
            id:content;width:parent.width;spacing:10
            RowLayout {
                Layout.fillWidth:true
                Text { text:"Уведомления";color:drawer.shell.colors.fg;font.pixelSize:18;font.bold:true;Layout.fillWidth:true }
                ActionButton { shell:drawer.shell;text:drawer.notificationState.dnd?"Не беспокоить: вкл.":"Не беспокоить";enabled:drawer.notificationState.available;onClicked:drawer.shell.notifications.act("dnd",!drawer.notificationState.dnd) }
            }
            RowLayout {
                ActionButton { shell:drawer.shell;text:"Текущие · "+drawer.notificationState.active.length;onClicked:drawer.history=false }
                ActionButton { shell:drawer.shell;text:"История · "+drawer.notificationState.history.length;onClicked:drawer.history=true }
                Item { Layout.fillWidth:true }
                ActionButton { shell:drawer.shell;text:"Убрать все";enabled:drawer.notificationState.available && !drawer.history && drawer.entries.length>0;onClicked:drawer.shell.notifications.act("clear",null) }
            }
            Text {
                Layout.fillWidth:true;wrapMode:Text.Wrap;textFormat:Text.PlainText
                visible:!!drawer.notificationState.error || drawer.entries.length===0
                text:drawer.notificationState.error || (drawer.history?"В истории пока пусто":"Новых уведомлений нет")
                color:drawer.shell.colors.fg_dim;font.pixelSize:13
            }
            Repeater {
                model:drawer.entries
                Rectangle {
                    id:card
                    required property var modelData
                    Layout.fillWidth:true;implicitHeight:message.implicitHeight+24
                    radius:12;color:Qt.alpha(drawer.shell.colors.fg,0.055)
                    border.width:modelData.urgency==="critical"?1:0;border.color:drawer.shell.colors.power_color
                    ColumnLayout {
                        id:message;anchors { left:parent.left;right:parent.right;top:parent.top;margins:12 }
                        spacing:6
                        RowLayout {
                            Layout.fillWidth:true
                            Text { text:card.modelData.app_name;Layout.fillWidth:true;elide:Text.ElideRight;textFormat:Text.PlainText;color:drawer.shell.colors.fg_dim;font.pixelSize:11 }
                            ActionButton { shell:drawer.shell;visible:!drawer.history;text:"×";Layout.preferredWidth:28;Layout.preferredHeight:28;onClicked:drawer.shell.notifications.act("dismiss",card.modelData.id) }
                        }
                        Text { Layout.fillWidth:true;text:card.modelData.summary;textFormat:Text.PlainText;wrapMode:Text.Wrap;color:drawer.shell.colors.fg;font.bold:true;font.pixelSize:14 }
                        Text { Layout.fillWidth:true;visible:!!text;text:card.modelData.body;textFormat:Text.PlainText;wrapMode:Text.Wrap;maximumLineCount:10;elide:Text.ElideRight;color:drawer.shell.colors.fg;font.pixelSize:13 }
                    }
                }
            }
            Text { visible:drawer.history;Layout.fillWidth:true;wrapMode:Text.Wrap;text:"Историю хранит Mako до перезапуска. Сообщения не записываются оболочкой на диск.";color:drawer.shell.colors.fg_dim;font.pixelSize:11 }
        }
    }
}
