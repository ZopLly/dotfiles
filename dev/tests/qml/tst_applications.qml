import QtQuick
import QtTest
import "../../../quickshell"
Item {
    width: 700; height: 600
    QtObject { id: testShell; property string openPanel:"applications"; property var applications:appData; property var colors: ({bg:"#17283a",fg:"#f3e7d0",fg_dim:"#a1aeb7",bg_modules:"#203447",accent:"#81b5d5"}) }
    QtObject {
        id:appData
        property string selectedGroup:""
        property bool currentOnly:false
        property var last:({})
        property var state:({usage:{"firefox.desktop":3,"Alacritty.desktop":2,"chatgpt.desktop":1}})
        function groupsFor(output) { return [
            {id:"first",name:"First",icon:"",windows:[{id:10,title:"First window",workspace_label:"1",is_focused:false,is_floating:false}]},
            {id:"second",name:"Second",icon:"",windows:[{id:20,title:"Second window",workspace_label:"2",is_focused:false,is_floating:false}]}
        ] }
        function act(action,value) { last={action:action,value:value} }
    }
    ApplicationsDrawer { id:drawer;anchors.fill:parent;visible:false;shell:testShell;outputName:"winit" }
    ApplicationsMenu {
        id: menu; anchors.fill: parent; shell: testShell
        entries: [{id:"Alacritty.desktop",name:"Alacritty",icon:""},{id:"firefox.desktop",name:"Firefox",icon:""},{id:"chatgpt.desktop",name:"ChatGPT",icon:""}]
        property string selected: ""
        onLaunch: id => selected=id
    }
    TestCase {
        name: "ApplicationInteraction"
        when: windowShown
        function init() { drawer.visible=false;menu.visible=true;menu.selected="";menu.reset();appData.last=({}) }
        function test_frequent_order_uses_measured_activity() {
            compare(menu.results[0].id,"firefox.desktop")
            appData.state=({usage:{"chatgpt.desktop":8,"Alacritty.desktop":2}})
            compare(menu.results[0].id,"chatgpt.desktop")
            appData.state=({usage:{"firefox.desktop":3,"Alacritty.desktop":2,"chatgpt.desktop":1}})
        }
        function test_search_enter_launches_match() {
            let search=findChild(menu,"applicationSearch")
            search.forceActiveFocus();keyClick(Qt.Key_F);keyClick(Qt.Key_I);keyClick(Qt.Key_R);keyClick(Qt.Key_E);keyClick(Qt.Key_Return)
            compare(menu.selected,"firefox.desktop")
        }
        function test_down_then_right_enter_launches_second_card() {
            let search=findChild(menu,"applicationSearch")
            search.forceActiveFocus();keyClick(Qt.Key_Down);keyClick(Qt.Key_Right);keyClick(Qt.Key_Return)
            compare(menu.selected,"Alacritty.desktop")
        }
        function test_empty_search_result_does_not_launch() {
            let search=findChild(menu,"applicationSearch")
            search.forceActiveFocus();keyClick(Qt.Key_Z);keyClick(Qt.Key_Z);keyClick(Qt.Key_Z);keyClick(Qt.Key_Return)
            compare(menu.selected,"")
        }
        function test_window_list_selection_is_visible_and_enter_uses_it() {
            menu.visible=false;drawer.visible=true
            let list=findChild(drawer,"windowGroups")
            verify(list!==null)
            list.forceActiveFocus();list.currentIndex=0
            verify(list.highlightItem!==null && list.highlightItem.visible)
            verify(list.highlightItem.color!==undefined && list.highlightItem.color.a>0 && list.highlightItem.opacity>0)
            let originalY=list.highlightItem.y
            keyClick(Qt.Key_Down)
            compare(list.currentIndex,1)
            tryVerify(() => list.highlightItem.y>originalY)
            keyClick(Qt.Key_Return)
            compare(appData.last.action,"focus");compare(appData.last.value,20)
        }

    }
}
