import QtQuick
import QtTest
import "../../../quickshell/appearance-ui"
Item {
    width: 900; height: 600
    QtObject {
        id: controller
        property bool busy: false
        property color bg: "#17283a"
        property color surface: "#203447"
        property color accent: "#81b5d5"
        property var last: ({})
        property var state: ({
            preview: true,
            selection: {palette_id: "legacy:test", mode: null, accent_id: null},
            themes: [
                {id:"legacy:test",label:"Original",group:"legacy",modes:[null],accents:[],adapted_modes:[],colors:{legacy:{bg:"#17283a",fg:"#ffffff",accent:"#81b5d5"}}},
                {id:"hyprstack:test",label:"Imported",group:"hyprstack",modes:["dark","light"],accents:[],adapted_modes:[],colors:{dark:{bg:"#111111",fg:"#ffffff",accent:"#6688cc"},light:{bg:"#ffffff",fg:"#111111",accent:"#2266bb"}}}
            ]
        })
        function choose(fields) { last=fields }
    }
    ThemeGrid { id: themes; anchors.fill: parent; appRoot: controller }
    TestCase {
        name: "AppearanceKeyboard"
        when: windowShown
        function init() { controller.last=({}) }
        function test_enter_selects_focused_theme() {
            let card=findChild(themes,"theme:legacy:test")
            verify(card !== null)
            card.forceActiveFocus()
            keyClick(Qt.Key_Return)
            compare(controller.last.palette_id,"legacy:test")
            compare(controller.last.mode,null)
        }
        function test_arrow_then_enter_selects_next_card() {
            let card=findChild(themes,"theme:legacy:test")
            card.forceActiveFocus()
            keyClick(Qt.Key_Right)
            keyClick(Qt.Key_Return)
            compare(controller.last.palette_id,"hyprstack:test")
            compare(controller.last.mode,"dark")
        }
    }
}
