pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Item {
    id: menu
    required property var shell
    property var entries: []
    property var usage: shell.applications.state?.usage || ({})
    property var results: {
        let query=search.text.trim().toLocaleLowerCase()
        return entries.filter(e => (e.name+" "+e.id).toLocaleLowerCase().includes(query)).slice().sort((a,b) => {
            if (query!=="") return a.name.localeCompare(b.name)
            return (usage[b.id] || 0)-(usage[a.id] || 0) || a.name.localeCompare(b.name)
        })
    }
    signal launch(string id)
    signal settings()
    function reset() { search.text=""; grid.currentIndex=0; search.forceActiveFocus() }
    ColumnLayout {
        anchors.fill: parent; spacing: 12
        RowLayout {
            Layout.fillWidth: true
            Text { text:"Приложения"; color:menu.shell.colors.fg; font.pixelSize:19; font.bold:true; Layout.fillWidth:true }
            ActionButton { shell:menu.shell; text:"Оформление"; onClicked:menu.settings() }
        }
        TextField {
            id: search; objectName:"applicationSearch"
            Layout.fillWidth:true; placeholderText:"Название приложения…"
            color:menu.shell.colors.fg; placeholderTextColor:menu.shell.colors.fg_dim; font.pixelSize:14
            selectByMouse:true
            background:Rectangle { radius:12; color:menu.shell.colors.bg; border.color:search.activeFocus?menu.shell.colors.accent:menu.shell.colors.fg_dim; border.width:1 }
            padding:12
            onTextChanged:grid.currentIndex=0
            onAccepted:if (menu.results.length) menu.launch(menu.results[0].id)
            Keys.onDownPressed: { grid.forceActiveFocus();grid.currentIndex=0 }
        }
        Text { text:search.text===""?"Чаще используемые — в начале списка":"Найдено: "+menu.results.length; color:menu.shell.colors.fg_dim; font.pixelSize:11 }
        GridView {
            id:grid; objectName:"applicationGrid"
            Layout.fillWidth:true; Layout.fillHeight:true; clip:true
            cellWidth:width/Math.max(1,Math.floor(width/120)); cellHeight:102
            model:menu.results; boundsBehavior:Flickable.StopAtBounds
            ScrollBar.vertical:ScrollBar {}
            keyNavigationEnabled:true; highlightMoveDuration:0
            Keys.onReturnPressed:if(currentIndex>=0 && currentIndex<count)menu.launch(menu.results[currentIndex].id)
            Keys.onEnterPressed:if(currentIndex>=0 && currentIndex<count)menu.launch(menu.results[currentIndex].id)
            delegate:Button {
                id:card
                required property var modelData
                required property int index
                width:grid.cellWidth-6; height:96
                background:Rectangle { radius:14; color:card.hovered || (grid.activeFocus && grid.currentIndex===card.index)?menu.shell.colors.accent:menu.shell.colors.bg; opacity:card.hovered || (grid.activeFocus && grid.currentIndex===card.index)?.4:1 }
                contentItem:Column {
                    spacing:8
                    AppIcon { anchors.horizontalCenter:parent.horizontalCenter; width:25;height:25; name:card.modelData.icon;label:card.modelData.name }
                    Text { width:parent.width; text:card.modelData.name; color:menu.shell.colors.fg; font.pixelSize:12; horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight }
                }
                onClicked:menu.launch(modelData.id)
            }
        }
        Text { visible:menu.results.length===0; text:"Подходящих приложений нет"; color:menu.shell.colors.fg_dim; Layout.alignment:Qt.AlignHCenter }
    }
}
