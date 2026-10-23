pragma ComponentBehavior: Bound
import QtQuick
Item {
    id: frame
    property color tint: "#89b4fa"
    property bool dragging: false
    signal started()
    signal resized(real newWidth, real newHeight, var rightAnchor, var bottomAnchor, bool final)
    function rectangle(edge,dx,dy,w,h) {
        return {width:Math.max(120,w+(edge.includes("w")?-dx:edge.includes("e")?dx:0)),
            height:Math.max(100,h+(edge.includes("n")?-dy:edge.includes("s")?dy:0))}
    }
    Repeater {
        model:["nw","n","ne","w","e","sw","s","se"]
        MouseArea {
            id: handle
            required property string modelData
            property bool leftEdge:modelData.includes("w")
            property bool topEdge:modelData.includes("n")
            property bool corner:modelData.length===2
            property point start
            property real oldWidth
            property real oldHeight
            property real rightAnchor
            property real bottomAnchor
            property var lastRect:({width:0,height:0})
            objectName:"resize-handle-"+modelData
            x:leftEdge?0:modelData.includes("e")?frame.width-width:14
            y:topEdge?0:modelData.includes("s")?frame.height-height:14
            width:corner?14:modelData==="n"||modelData==="s"?Math.max(0,frame.width-28):7
            height:corner?14:modelData==="w"||modelData==="e"?Math.max(0,frame.height-28):7
            hoverEnabled:true
            acceptedButtons:Qt.LeftButton
            preventStealing:true
            cursorShape:corner?(modelData==="nw"||modelData==="se"?Qt.SizeFDiagCursor:Qt.SizeBDiagCursor):(modelData==="w"||modelData==="e"?Qt.SizeHorCursor:Qt.SizeVerCursor)
            Rectangle {anchors.fill:parent;radius:3;color:Qt.alpha(frame.tint,handle.pressed?.45:.15);visible:handle.containsMouse||handle.pressed}
            onPressed:function(mouse) {
                start=mapToItem(null,mouse.x,mouse.y)
                oldWidth=frame.width;oldHeight=frame.height
                rightAnchor=frame.x+frame.width;bottomAnchor=frame.y+frame.height
                lastRect={width:oldWidth,height:oldHeight}
                frame.started()
                frame.dragging=true
            }
            onPositionChanged:function(mouse) {
                if(!pressed)return
                let point=mapToItem(null,mouse.x,mouse.y)
                lastRect=frame.rectangle(modelData,point.x-start.x,point.y-start.y,oldWidth,oldHeight)
                frame.resized(lastRect.width,lastRect.height,leftEdge?rightAnchor:null,topEdge?bottomAnchor:null,false)
            }
            onReleased:{frame.resized(lastRect.width,lastRect.height,leftEdge?rightAnchor:null,topEdge?bottomAnchor:null,true);frame.dragging=false}
            onCanceled:frame.dragging=false
        }
    }
}
