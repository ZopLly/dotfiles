import QtQuick
import QtTest
import "../../../quickshell"
Item {
 width:390;height:300
 QtObject {
  id:stub
  property var state:({battery:{percent:50,status:"Discharging",level:"discharging",remaining_text:"≈ 2 ч 30 мин до разряда"},profiles:[],available:false})
  property var colors:({bg:"#17283a",fg:"#ffffff",fg_dim:"#a1aeb7",accent:"#81b5d5"})
 }
 PowerModule {id:power;width:380;shell:stub;outputName:"winit"}
 TestCase {
  name:"BatteryRemaining";when:windowShown
  function test_estimate_is_visible_and_disappears_when_unavailable() {
   let label=findChild(power,"battery-remaining")
   verify(label.visible);compare(label.text,"≈ 2 ч 30 мин до разряда")
   stub.state={battery:{percent:50,status:"Charging",level:"charging"},profiles:[],available:false}
   compare(label.text,"");verify(!label.visible)
  }
 }
}
