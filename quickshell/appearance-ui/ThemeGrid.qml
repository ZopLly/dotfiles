pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: root
    required property var appRoot
    spacing: 10
    TextField { id: search; Layout.fillWidth: true; font.pixelSize: 14; padding: 12; placeholderText: "Найти тему"; Accessible.name: "Поиск темы" }
    Label { text: "4 прежние темы Niri · 18 палитр Hyprstack"; opacity: 0.7; font.pixelSize: 12 }
    GridView {
        id: grid
        Layout.fillWidth: true; Layout.fillHeight: true
        clip: true; reuseItems: true
        cellWidth: width >= 720 ? width/3 : width >= 460 ? width/2 : width
        cellHeight: 172
        model: (root.appRoot.state.themes || []).filter(t => t.label.toLowerCase().includes(search.text.toLowerCase()))
        ScrollBar.vertical: ScrollBar {}
        delegate: Button {
            id: card
            objectName: "theme:"+modelData.id
            required property var modelData
            required property int index
            width: grid.cellWidth-10; height: grid.cellHeight-10
            enabled: !root.appRoot.busy && (root.appRoot.state.enabled ?? root.appRoot.state.preview)
            Accessible.name: modelData.label
            background: Rectangle {
                radius: 12; color: root.appRoot.surface
                border.width: card.activeFocus || card.modelData.id === root.appRoot.state.selection.palette_id ? 2 : 1
                border.color: card.activeFocus || card.modelData.id === root.appRoot.state.selection.palette_id ? root.appRoot.accent : Qt.rgba(0.5,0.5,0.5,0.15)
            }
            contentItem: ColumnLayout {
                spacing: 8
                Label { text: card.modelData.label; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                Label { text: card.modelData.group === "legacy" ? "Прежняя тема Niri" : "Hyprstack"; font.pixelSize: 11; opacity: 0.65 }
                RowLayout {
                    Layout.fillWidth: true
                    Repeater {
                        model: Object.keys(card.modelData.colors)
                        Rectangle {
                            required property string modelData
                            Layout.fillWidth: true; Layout.preferredHeight: 40
                            radius: 7; color: card.modelData.colors[modelData].bg
                            Rectangle { anchors.centerIn: parent; width: 34; height: 12; radius: 4; color: card.modelData.colors[parent.modelData].accent }
                        }
                    }
                }
                Label {
                    Layout.fillWidth: true; font.pixelSize: 11; opacity: 0.75; elide: Text.ElideRight
                    text: card.modelData.adapted_modes.length ? "Светлый вариант адаптирован" : card.modelData.group === "legacy" ? "Исходные цвета сохранены" : "Тёмный и светлый варианты"
                }
            }
            onClicked: {
                let same = modelData.id === root.appRoot.state.selection.palette_id
                root.appRoot.choose({palette_id: modelData.id, mode: modelData.group === "legacy" ? null : (same ? root.appRoot.state.selection.mode : "dark"), accent_id: same ? root.appRoot.state.selection.accent_id : null})
            }
            Keys.onReturnPressed: clicked()
            Keys.onEnterPressed: clicked()
            Keys.onRightPressed: { grid.currentIndex = Math.min(grid.count-1,index+1); grid.currentItem.forceActiveFocus() }
            Keys.onLeftPressed: { grid.currentIndex = Math.max(0,index-1); grid.currentItem.forceActiveFocus() }
            Keys.onDownPressed: { grid.currentIndex = Math.min(grid.count-1,index+Math.round(grid.width/grid.cellWidth)); grid.currentItem.forceActiveFocus() }
            Keys.onUpPressed: { grid.currentIndex = Math.max(0,index-Math.round(grid.width/grid.cellWidth)); grid.currentItem.forceActiveFocus() }
        }
    }
}
