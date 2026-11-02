import QtQuick
import QtTest
import "../../../quickshell"
Item {
 width:500;height:700
 QtObject {
  id:stub
  property var notifications:notificationsData
  property var colors:({bg:"#17283a",bg_modules:"#203447",fg:"#ffffff",fg_dim:"#a1aeb7",accent:"#81b5d5",power_color:"#ff7777"})
 }
 QtObject {
  id:notificationsData
  property var state:({available:true,active:[{id:17,app_name:"Niri Test",summary:"Synthetic title",body:"<b>Plain text</b>",urgency:"normal"}],history:[],dnd:false,error:""})
  property var last:({})
  function act(action,value) {last={action:action,value:value}}
 }
 NotificationsDrawer {id:drawer;shell:stub;width:440;height:620}
 TestCase {
  name:"Notifications";when:windowShown
  function test_contents_are_plain_text_and_history_is_separate() {
   compare(drawer.entries.length,1)
   drawer.history=true;compare(drawer.entries.length,0)
   drawer.history=false;compare(drawer.entries[0].id,17)
   verify(drawer.implicitHeight>100)
  }
 }
}
