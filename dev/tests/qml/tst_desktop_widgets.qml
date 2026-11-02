import QtQuick
import QtQuick.Layouts
import QtTest
import "../../../quickshell"
Rectangle {
    id: canvas
    width: 720; height: 460; color: "#17283a"
    QtObject {
        id: stub
        property var colors: ({bg:"#17283a",bg_modules:"#203447",fg:"#f3e7d0",fg_dim:"#b9c6cf",accent:"#81b5d5"})
        property date now: new Date(2026,9,22,21,20)
        property var state: ({preview:true})
        property var player: null
        property var players: []
        property var weather: ({temperature:18,feels:17,code:0,preview:true})
        property var dashboard: data
    }
    QtObject {
        id: data
        property var metrics: ({cpu:23,memory:46})
        property var samples: Array.from({length:90},(_,i)=>({cpu:24+Math.sin(i/7)*19,memory:46}))
    }
    WidgetFrame { x:20;y:20;width:320;height:180;shell:stub;DesktopClock {anchors.centerIn:parent;width:288;shell:stub} }
    WidgetFrame { x:370;y:20;width:320;height:180;shell:stub;LoadWidget {id:load;anchors.fill:parent;anchors.margins:18;shell:stub} }
    WidgetFrame { x:20;y:220;width:320;height:180;shell:stub;WeatherCard {anchors.fill:parent;anchors.margins:18;shell:stub;compact:true} }
    WidgetFrame { x:370;y:220;width:320;height:180;shell:stub;MediaCard {anchors.fill:parent;anchors.margins:18;shell:stub;compact:true} }
    SpectrumBars {id:spectrum;x:20;y:410;width:670;height:32;levels:[.2,.6,.4,.8,1,.5,.3,.7,.9,.4,.1,.2,.6,.8,.4,.5,.7,.3,.2,.1];tint:stub.colors.accent}
    TestCase {
        name: "DesktopWidgets"; when: windowShown
        function test_values_and_absent_readings() {
            compare(findChild(load,"load-value-cpu").text,"23%")
            compare(findChild(load,"load-value-memory").text,"46%")
            data.metrics={cpu:null,memory:0}
            compare(findChild(load,"load-value-cpu").text,"—")
            compare(findChild(load,"load-value-memory").text,"0%")
            data.metrics={cpu:23,memory:46}
            spectrum.levels=[2,-1,"bad"];wait(100)
            compare(findChild(spectrum,"spectrum-bar-0").height,32)
            compare(findChild(spectrum,"spectrum-bar-1").height,3)
            compare(findChild(spectrum,"spectrum-bar-2").height,3)
        }
        function test_render() {
            spectrum.levels=[.2,.6,.4,.8,1,.5,.3,.7,.9,.4,.1,.2,.6,.8,.4,.5,.7,.3,.2,.1]
            wait(150)
            let done=false
            canvas.grabToImage(r=>{r.saveToFile("/tmp/niri-desktop-widgets.png");done=true})
            tryVerify(()=>done)
        }
    }
}
