import QtQuick
import QtTest
import "../../../quickshell"
Item {
 width:700;height:100
 QtObject {
  id:stub
  property var colors:({bg:"#17283a",bg_modules:"#203447",fg:"#ffffff",fg_dim:"#a1aeb7",accent:"#81b5d5"})
  property var applications:appData
  property var last:({})
  property var workspaces:[{id:42,idx:1,output:"winit",is_active:true},{id:99,idx:2,output:"winit",is_active:false},{id:101,idx:3,output:"winit",is_active:false}]
  function send(action,args) {last={action:action,args:args}}
 }
 QtObject {
  id:appData
  property var last:({})
  property var state:({groups:[{id:"terminal",name:"Terminal",icon:"",windows:[{id:7,title:"One",workspace_id:42,is_focused:true},{id:8,title:"Two",workspace_id:42,is_focused:false},{id:9,title:"Three",workspace_id:99,is_focused:false}]}]})
  function act(action,value) {last={action:action,value:value}}
  function toggle(panel,output,group) {last={panel:panel,output:output}}
 }
 WorkspaceIsland {id:island;shell:stub;outputName:"winit";maxWidth:400}
 TestCase {
  name:"UnifiedWorkspaces";when:windowShown
  function test_windows_are_individual_targets_inside_workspaces() {
   let first=findChild(island,"workspace-window:7"),second=findChild(island,"workspace-window:8")
   verify(first!==null && second!==null)
   mouseClick(second);compare(appData.last.action,"focus");compare(appData.last.value,8)
   let empty=findChild(island,"workspace:101");verify(empty!==null)
   mouseClick(empty);compare(stub.last.args.index,3)
  }
  function test_narrow_island_remains_bounded_and_has_overflow() {
   island.maxWidth=140
   verify(island.width<=140)
   let overflow=findChild(island,"workspace-overflow")
   verify(overflow.visible)
   mouseClick(overflow);compare(appData.last.panel,"applications")
   island.maxWidth=400
  }
 }
}
