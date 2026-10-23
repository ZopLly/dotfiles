pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
Rectangle {
    id:tile
    required property var shell
    default property alias contents:body.data
    property string title:""
    implicitHeight:body.implicitHeight+48
    radius:24
    color:Qt.alpha(shell.colors.fg,0.045)
    border.color:Qt.alpha(shell.colors.fg,0.09);border.width:1
    data: ColumnLayout {
        id:body
        anchors {left:parent.left;right:parent.right;top:parent.top;margins:20}
        spacing:14
        Text { visible:tile.title!=="";text:tile.title;color:tile.shell.colors.fg_dim;font.pixelSize:12;font.weight:Font.Medium;Layout.fillWidth:true }
    }
}
