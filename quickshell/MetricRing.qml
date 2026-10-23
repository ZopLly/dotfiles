pragma ComponentBehavior: Bound
import QtQuick
Item {
    id:ring
    required property var shell
    property var value:null
    property string caption:""
    property string suffix:"%"
    implicitWidth:86;implicitHeight:108
    onValueChanged:circle.requestPaint()
    Connections { target:ring.shell;function onColorsChanged() {circle.requestPaint()} }
    Canvas {
        id:circle;width:76;height:76;anchors.horizontalCenter:parent.horizontalCenter
        onPaint: {
            let ctx=getContext("2d");ctx.reset();ctx.lineWidth=5;ctx.lineCap="round"
            ctx.strokeStyle=Qt.alpha(ring.shell.colors.fg,0.10)
            ctx.beginPath();ctx.arc(38,38,32,0,2*Math.PI);ctx.stroke()
            if (typeof ring.value === "number" && isFinite(ring.value)) {
                ctx.strokeStyle=ring.shell.colors.accent;ctx.beginPath()
                ctx.arc(38,38,32,-Math.PI/2,-Math.PI/2+2*Math.PI*Math.max(0,Math.min(100,ring.value))/100);ctx.stroke()
            }
        }
        Text { anchors.centerIn:parent;text:typeof ring.value === "number"?Math.round(ring.value)+ring.suffix:"—";color:ring.shell.colors.fg;font.pixelSize:17;font.weight:Font.DemiBold }
    }
    Text { anchors {top:circle.bottom;topMargin:10;horizontalCenter:parent.horizontalCenter} text:ring.caption;color:ring.shell.colors.fg_dim;font.pixelSize:11 }
}
