pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
ComboBox {
    id: choice
    required property var shell
    implicitHeight: 40
    leftPadding: 12
    contentItem: Text { text: choice.displayText; color: choice.shell.colors.fg; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; font.pixelSize: 12 }
    background: Rectangle { radius: 12; color: choice.shell.colors.surface || choice.shell.colors.bg; border.width: choice.activeFocus ? 1 : 0; border.color: choice.shell.colors.accent }
    delegate: ItemDelegate {
        required property var modelData
        width: choice.width
        contentItem: Text { text: modelData; color: choice.shell.colors.fg; font.pixelSize: 12 }
        background: Rectangle { color: parent.hovered ? (choice.shell.colors.hover || choice.shell.colors.fg_dim) : (choice.shell.colors.surface || choice.shell.colors.bg) }
    }
    popup: Popup {
        y: choice.height+4; width: choice.width
        implicitHeight: Math.min(240, contentItem.implicitHeight+12)
        padding: 6
        background: Rectangle { radius: 12; color: choice.shell.colors.surface || choice.shell.colors.bg; border.color: choice.shell.colors.accent }
        contentItem: ListView { clip: true; implicitHeight: contentHeight; model: choice.popup.visible ? choice.delegateModel : null; currentIndex: choice.highlightedIndex }
    }
}
