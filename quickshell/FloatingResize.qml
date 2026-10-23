pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
PanelWindow {
    id: overlay
    required property var shell
    required property string outputName
    property var windows:(shell.applications.state.groups || []).reduce((all,g)=>all.concat(g.windows || []),[])
    property var candidate:(windows || []).find(w=>w.is_floating && w.is_focused && w.output===overlay.outputName && w.layout?.tile_pos_in_workspace_view) || null
    property var heldWindow:null
    property bool heldAlive:!!heldWindow && (windows || []).some(w=>w.id===heldWindow.id && w.is_floating && w.output===overlay.outputName)
    property var target:grips.dragging?heldWindow:candidate
    property var geometry:target?.layout || {}
    property var pos:geometry.tile_pos_in_workspace_view || [0,0]
    property var offset:geometry.window_offset_in_tile || [0,0]
    property var size:geometry.window_size || [0,0]
    property var pending:null
    anchors {top:true;bottom:true;left:true;right:true}
    exclusionMode:ExclusionMode.Ignore
    color:"transparent"
    visible:!!target && (!grips.dragging || heldAlive) && shell.openPanel==="" && !shell.editMode
    WlrLayershell.layer:WlrLayer.Top
    WlrLayershell.namespace:"niri-shell-floating-resize"
    WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
    mask:Region {
        x:grips.x;y:grips.y;width:grips.width;height:7
        Region{x:grips.x;y:grips.y+grips.height-7;width:grips.width;height:7}
        Region{x:grips.x;y:grips.y;width:7;height:grips.height}
        Region{x:grips.x+grips.width-7;y:grips.y;width:7;height:grips.height}
        Region{x:grips.x;y:grips.y;width:14;height:14}
        Region{x:grips.x+grips.width-14;y:grips.y;width:14;height:14}
        Region{x:grips.x;y:grips.y+grips.height-14;width:14;height:14}
        Region{x:grips.x+grips.width-14;y:grips.y+grips.height-14;width:14;height:14}
    }
    ResizeFrame {
        id:grips
        x:overlay.pos[0]+overlay.offset[0];y:overlay.pos[1]+overlay.offset[1]
        width:overlay.size[0];height:overlay.size[1]
        tint:overlay.shell.colors.accent
        onStarted:overlay.heldWindow=overlay.candidate
        onResized:function(w,h,right,bottom,final) {
            if(!overlay.target)return
            overlay.pending={id:overlay.target.id,pid:overlay.target.pid,output:overlay.outputName,width:w,height:h,right:right,bottom:bottom,final:final}
            if(final){throttle.stop();overlay.flush()}else if(!throttle.running)throttle.start()
        }
    }
    onVisibleChanged:if(!visible){throttle.stop();pending=null}
    function flush(){if(pending && visible){worker.write(JSON.stringify(pending)+"\n");pending=null}}
    Timer{id:throttle;interval:33;onTriggered:overlay.flush()}
    Process {
        id:worker;running:overlay.visible;stdinEnabled:true
        command:["python3",Quickshell.shellDir+"/floating_resize.py"]
        stdout:SplitParser {onRead:line=>{try{let event=JSON.parse(line);if(event.error)console.warn("Floating resize:",event.error)}catch(e){}}}
    }
}
