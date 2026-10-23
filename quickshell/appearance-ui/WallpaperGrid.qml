pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: root
    required property var appRoot
    spacing: 10
    TextField { id: search; Layout.fillWidth: true; font.pixelSize: 14; padding: 12; placeholderText: "Найти обои"; Accessible.name: "Поиск обоев" }
    Label { text: "Все 11 обоев · выбор не меняет палитру"; opacity: 0.7; font.pixelSize: 12 }
    GridView {
        id: grid
        Layout.fillWidth: true; Layout.fillHeight: true
        clip: true; reuseItems: true
        cellWidth: width >= 720 ? width/3 : width >= 460 ? width/2 : width
        cellHeight: 205
        model: (root.appRoot.state.wallpapers || []).filter(w => w.label.toLowerCase().includes(search.text.toLowerCase()))
        ScrollBar.vertical: ScrollBar {}
        delegate: Button {
            id: card
            objectName: "wallpaper:"+modelData.id
            required property var modelData
            required property int index
            width: grid.cellWidth-10; height: grid.cellHeight-10
            enabled: !root.appRoot.busy && (root.appRoot.state.enabled ?? root.appRoot.state.preview)
            Accessible.name: modelData.label
            background: Rectangle {
                radius: 12; color: root.appRoot.surface
                border.width: card.activeFocus || (root.appRoot.state.wallpaper_status !== 'unconfirmed' && card.modelData.id === root.appRoot.state.selection.wallpaper_id) ? 2 : 1
                border.color: card.activeFocus || (root.appRoot.state.wallpaper_status !== 'unconfirmed' && card.modelData.id === root.appRoot.state.selection.wallpaper_id) ? root.appRoot.accent : Qt.rgba(0.5,0.5,0.5,0.15)
            }
            contentItem: ColumnLayout {
                spacing: 6
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    color: root.appRoot.bg; radius: 8; clip: true
                    Image {
                        anchors.fill: parent; asynchronous: true
                        source: root.appRoot.thumbnails[card.modelData.id] || card.modelData.thumbnail_url || ""
                        sourceSize: Qt.size(520,320)
                        fillMode: Image.PreserveAspectCrop
                    }
                    Label { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 8; text: card.modelData.frames > 1 ? "GIF" : ""; color: "#ffffff"; font.bold: true; style: Text.Outline; styleColor: "#000000" }
                }
                Label { text: card.modelData.label; Layout.fillWidth: true; elide: Text.ElideRight; font.pixelSize: 13 }
                Label { text: card.modelData.width+" × "+card.modelData.height; font.pixelSize: 11; opacity: 0.65 }
            }
            Component.onCompleted: root.appRoot.thumbnail(modelData.id)
            onModelDataChanged: root.appRoot.thumbnail(modelData.id)
            onClicked: root.appRoot.choose({wallpaper_id: modelData.id})
            Keys.onReturnPressed: clicked()
            Keys.onEnterPressed: clicked()
            Keys.onRightPressed: { grid.currentIndex = Math.min(grid.count-1,index+1); grid.currentItem.forceActiveFocus() }
            Keys.onLeftPressed: { grid.currentIndex = Math.max(0,index-1); grid.currentItem.forceActiveFocus() }
            Keys.onDownPressed: { grid.currentIndex = Math.min(grid.count-1,index+Math.round(grid.width/grid.cellWidth)); grid.currentItem.forceActiveFocus() }
            Keys.onUpPressed: { grid.currentIndex = Math.max(0,index-Math.round(grid.width/grid.cellWidth)); grid.currentItem.forceActiveFocus() }
        }
    }
}
