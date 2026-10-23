pragma ComponentBehavior: Bound
import QtQuick
Item {
    id: icon
    property string name: ""
    property string label: ""
    implicitWidth: 24; implicitHeight: 24
    Image {
        id: image
        anchors.fill: parent
        source: icon.name === "" ? "" : icon.name.includes(":") ? icon.name : "image://icon/"+encodeURIComponent(icon.name)
        sourceSize.width: Math.max(16,Math.min(128,Math.ceil(width*2))); sourceSize.height: Math.max(16,Math.min(128,Math.ceil(height*2)))
        fillMode: Image.PreserveAspectFit
        smooth: true
    }
    Text {
        anchors.centerIn: parent
        visible: image.source.toString()==="" || image.status===Image.Error
        text: icon.label.slice(0,1).toUpperCase() || "◻"
        font.pixelSize: 18; font.bold: true; color: "#a8bdd0"
    }
}
