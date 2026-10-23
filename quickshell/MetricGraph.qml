pragma ComponentBehavior: Bound
import QtQuick
Item {
    id:graph
    required property var shell
    property var samples:[]
    property string field:"cpu"
    implicitHeight:100
    onSamplesChanged:plot.requestPaint()
    onWidthChanged:plot.requestPaint()
    Connections {target:graph.shell;function onColorsChanged(){plot.requestPaint()} }
    Canvas {
        id:plot;anchors.fill:parent
        onPaint:{
            let ctx=getContext("2d");ctx.reset()
            ctx.lineWidth=1;ctx.strokeStyle=Qt.alpha(graph.shell.colors.fg,0.1)
            for(let n=0;n<3;n++){let y=4+(height-8)*n/2;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(width,y);ctx.stroke()}
            ctx.strokeStyle=graph.shell.colors.accent;ctx.lineWidth=2;ctx.lineJoin="round";ctx.beginPath()
            let started=false
            graph.samples.forEach((s,i)=>{
                let v=s[graph.field]
                if(typeof v!=="number" || !isFinite(v)){started=false;return}
                let x=width*(i/89),y=height-4-(height-8)*Math.max(0,Math.min(100,v))/100
                if(started)ctx.lineTo(x,y);else ctx.moveTo(x,y)
                started=true
            });ctx.stroke()
        }
    }
}
