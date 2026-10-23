import QtQuick
import QtTest
import "../../quickshell"
Rectangle {
 id:canvas;width:880;height:1100;color:"#17283a"
 QtObject {
  id:stub
  property var colors:({bg:"#17283a",bg_modules:"#203447",fg:"#f3e7d0",fg_dim:"#b9c6cf",accent:"#81b5d5",power_color:"#ff9990"})
  property date now:new Date(2026,9,22,21,20)
  property var state:({preview:true,battery:{percent:78}})
  property var workspaces:[{id:42,idx:1,name:"Разработка",output:"winit",is_active:true}]
  property var applications:apps
  property var dashboard:metrics
  property var calendarState:({configured:false,events:[]})
  property var weather:({preview:true,temperature:18,feels:17,code:0,days:[]})
  property var players:[]
  property var player:null
  property string editorPanel:""
  function panelModules(panel) {return []}
 }
 QtObject {id:apps;property var state:({groups:[]});function act(action,value){} }
 QtObject {
  id:metrics
  property string section:"overview"
  property var metrics:({cpu:23,memory:46,memory_used:7902739824,memory_total:17179869184,uptime:12345,cores:16,load:1.25,swap:0})
  property var samples:Array.from({length:70},(_,i)=>({cpu:18+Math.sin(i/8)*12,memory:46+i/50}))
  property string error:""
 }
 Dashboard {id:dashboard;x:20;y:20;width:canvas.width-40;height:implicitHeight;outputName:"winit";shell:stub}
 TestCase {
  name:"Dashboard";when:windowShown
  function test_1_sections_and_missing_metrics() {
   compare(dashboard.currentTab,"overview")
   compare(dashboard.space.id,42)
   compare(dashboard.desktopWindows.length,0)
   compare(dashboard.percent(null),"—")
   mouseClick(findChild(dashboard,"dashboard-tab-performance"));compare(dashboard.currentTab,"performance")
   mouseClick(findChild(dashboard,"dashboard-tab-weather"));compare(dashboard.currentTab,"weather")
   mouseClick(findChild(dashboard,"dashboard-tab-media"));compare(dashboard.currentTab,"media")
   mouseClick(findChild(dashboard,"dashboard-tab-overview"));compare(dashboard.currentTab,"overview")
  }
  function test_2_narrow_panel_stacks_cards() {
   canvas.width=460;wait(100);verify(!dashboard.wide)
   verify(dashboard.implicitHeight>700)
   canvas.width=880;wait(100);verify(dashboard.wide)
  }
  function test_3_render_preview() {
   metrics.section="overview";wait(100)
   let done=false
   canvas.grabToImage(r=>{r.saveToFile("/tmp/niri-dashboard-overview.png");done=true})
   tryVerify(()=>done)
   metrics.section="performance";wait(100);done=false
   canvas.grabToImage(r=>{r.saveToFile("/tmp/niri-dashboard-performance.png");done=true})
   tryVerify(()=>done)
  }
 }
}
