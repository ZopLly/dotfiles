pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
Scope {
    id:controller
    required property var shell
    property string section:"overview"
    property var metrics: ({})
    property var samples: []
    property string error: ""
    property bool active: shell.openPanel === "center" || (shell.workspaces || []).some(w =>
        w.is_active && w.output && shell.widgetVisible(w.output, "metrics"))
    onActiveChanged: if (!active) { metrics=({});samples=[];error="" }
    IpcHandler {
        target:"dashboard"
        function page(name:string):void {
            if (!["overview","media","performance","weather","modules"].includes(name)) return
            controller.section=name
            controller.shell.openScreen=controller.shell.osdScreen
            controller.shell.openPanel="center"
        }
        function status():string {return JSON.stringify({active:controller.active,section:controller.section,samples:controller.samples.length,metrics:controller.metrics,error:controller.error})}
    }
    Process {
        command:["python3",Quickshell.shellDir+"/system_metrics.py"]
        running:controller.active
        stdout:SplitParser { onRead:line => {
            if (!controller.active) return
            try {
                controller.metrics=JSON.parse(line)
                controller.samples=controller.samples.concat([controller.metrics]).slice(-90)
                controller.error=""
            } catch(e) { controller.error="Показатели системы пока недоступны" }
        } }
    }
}
