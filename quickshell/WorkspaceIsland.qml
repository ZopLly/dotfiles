pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import "WorkspaceModel.js" as Workspaces
Rectangle {
 id:island
 required property var shell
 required property string outputName
 property real maxWidth:400
 property var groups:Workspaces.groups(shell.workspaces || shell.state.workspaces || [],shell.applications.state.groups,outputName)
 property real naturalWidth:48+groups.reduce((sum,g)=>sum+g.width+4,0)+8
 property bool overflow:naturalWidth>maxWidth
 implicitWidth:naturalWidth
 width:Math.min(naturalWidth,maxWidth);height:40;radius:20;color:shell.colors.bg_modules
 function revealActive() {
  let x=0
  for(let group of groups) {
   if(group.is_active) {
    scroll.contentX=Math.max(0,Math.min(scroll.contentWidth-scroll.width,Math.max(x+group.width-scroll.width,Math.min(scroll.contentX,x))))
    return
   }
   x+=group.width+4
  }
 }
 onGroupsChanged:Qt.callLater(revealActive)
 onWidthChanged:Qt.callLater(revealActive)
 ActionButton {
  id:launcher;x:4;y:2;width:40;height:36;implicitWidth:40;quiet:true
  shell:island.shell;text:"󰣇"
  onClicked:island.shell.applications.toggle("launcher",island.outputName)
 }
 Flickable {
  id:scroll;x:48;y:2;width:Math.max(0,island.width-56-(island.overflow?32:0));height:36
  contentWidth:workspaceRow.width;contentHeight:36;clip:true
  flickableDirection:Flickable.HorizontalFlick;boundsBehavior:Flickable.StopAtBounds
  WheelHandler {
   onWheel:event => {
    let delta=event.pixelDelta.x || event.pixelDelta.y || event.angleDelta.x/3 || event.angleDelta.y/3
    scroll.contentX=Math.max(0,Math.min(scroll.contentWidth-scroll.width,scroll.contentX-delta));event.accepted=true
   }
  }
  Row {
   id:workspaceRow;spacing:4;height:36
   Repeater {
    model:island.groups
    Rectangle {
     id:space
     required property var modelData
     objectName:"workspace-group:"+modelData.id
     width:modelData.width;height:36;radius:16
     color:modelData.is_active?Qt.alpha(island.shell.colors.accent,.24):island.shell.colors.bg
     border.width:modelData.is_active?1:0;border.color:island.shell.colors.accent
     Behavior on color {ColorAnimation {duration:140}}
     MouseArea {anchors.fill:parent;onClicked:island.shell.send("workspace",{index:space.modelData.idx,output:island.outputName})}
     Row {
      anchors.centerIn:parent
      Repeater {
       model:space.modelData.windows
       Button {
        id:windowButton
        required property var modelData
        objectName:"workspace-window:"+modelData.id
        width:32;height:32
        ToolTip.visible:hovered
        ToolTip.text:(modelData.title || modelData.name)+" · Стол "+space.modelData.idx
        background:Rectangle {radius:11;color:windowButton.hovered?Qt.alpha(island.shell.colors.accent,.25):"transparent"}
        contentItem:Item {
         AppIcon {anchors.centerIn:parent;width:16;height:16;name:windowButton.modelData.icon;label:windowButton.modelData.name}
         Rectangle {anchors.bottom:parent.bottom;anchors.horizontalCenter:parent.horizontalCenter;width:14;height:2;radius:1;color:island.shell.colors.accent;visible:!!windowButton.modelData.is_focused}
         Rectangle {anchors.top:parent.top;anchors.right:parent.right;width:5;height:5;radius:3;color:island.shell.colors.power_color || island.shell.colors.accent;visible:!!windowButton.modelData.is_urgent}
        }
        onClicked:island.shell.applications.act("focus",modelData.id)
        Keys.onReturnPressed:clicked()
        Keys.onEnterPressed:clicked()
        TapHandler {acceptedButtons:Qt.RightButton;onTapped:island.shell.applications.toggle("applications",island.outputName,windowButton.modelData.groupId)}
       }
      }
      Button {
       id:empty
       objectName:"workspace:"+space.modelData.id
       visible:space.modelData.windows.length===0;width:28;height:32
       ToolTip.visible:hovered;ToolTip.text:"Стол "+space.modelData.idx
       background:Item {}
       contentItem:Item {Rectangle {anchors.centerIn:parent;width:space.modelData.is_active?9:6;height:width;radius:width/2;color:space.modelData.is_active?island.shell.colors.accent:island.shell.colors.fg_dim}}
       onClicked:island.shell.send("workspace",{index:space.modelData.idx,output:island.outputName})
       Keys.onReturnPressed:clicked()
      }
     }
    }
   }
  }
 }
 ActionButton {
  objectName:"workspace-overflow"
  anchors.right:parent.right;anchors.rightMargin:4;y:2;width:32;height:36;implicitWidth:32
  shell:island.shell;text:"•••";quiet:true;visible:island.overflow
  onClicked:island.shell.applications.toggle("applications",island.outputName)
 }
}
