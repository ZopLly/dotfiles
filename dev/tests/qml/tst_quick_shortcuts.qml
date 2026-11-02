import QtQuick
import QtTest
import "../../../quickshell"
Item {
 width:390;height:300
 QtObject {
  id:stub
  property var applications:appData
  property var state:({vpns:[]})
  property var colors:({bg:"#17283a",bg_modules:"#203447",fg:"#ffffff",fg_dim:"#a1aeb7",accent:"#81b5d5"})
 }
 QtObject {
  id:appData
  property var entries:[{id:"Happ.desktop"}]
  property bool busy:false
  property var state:({workspaces:[{id:42,output:"winit",is_active:true,is_focused:true}],window_modes:{}})
  property var last:({})
  function act(action,value) {last={action:action,value:value}}
 }
 QuickSettingsHeader {id:header;width:380;shell:stub}
 VpnModule {id:vpn;y:100;width:380;shell:stub;outputName:"winit"}
 TestCase {
  name:"QuickShortcuts";when:windowShown
  function test_settings_and_installed_vpn_have_direct_actions() {
   mouseClick(findChild(header,"quick-appearance"));compare(appData.last.action,"settings")
   mouseClick(findChild(header,"workspace-mode"));compare(appData.last.action,"workspace-mode")
   mouseClick(findChild(vpn,"open-happ"));compare(appData.last.action,"launch");compare(appData.last.value,"Happ.desktop")
  }
 }
}
