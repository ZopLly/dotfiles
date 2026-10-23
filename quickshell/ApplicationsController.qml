pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
Scope {
    id: apps
    required property var shell
    property var entries: []
    property var state: ({groups:[],workspaces:[],preview:true})
    property bool currentOnly: false
    property string selectedGroup: ""
    property string error: ""
    property bool busy: false
    function iconUrl(name) { return !name || name.includes(":") ? name : Quickshell.iconPath(name,true).toString() }
    function groupsFor(output) {
        if (!currentOnly) return state.groups || []
        let active=(state.workspaces || []).find(w => w.output===output && w.is_active)
        if (!active) return []
        return (state.groups || []).map(g => Object.assign({},g,{windows:g.windows.filter(w => w.workspace_id===active.id)})).filter(g => g.windows.length)
    }
    function toggle(panel,output,group) {
        let closing=shell.openPanel===panel && shell.openScreen===output && selectedGroup===(group || "")
        shell.openScreen=output; selectedGroup=group || ""; shell.openPanel=closing?"":panel
    }
    function act(action,value) {
        if (busy) return
        busy=true;error=""
        backend.write(JSON.stringify({action:action,value:value})+"\n")
        if (["focus","launch","settings"].includes(action)) shell.openPanel=""
    }
    Process {
        id:backend
        command:["python3",Quickshell.shellDir+"/applications/bridge.py"]
        stdinEnabled:true;running:true
        stdout:SplitParser {
            onRead:data => {
                try {
                    let event=JSON.parse(data)
                    if(event.type==="catalogue")apps.entries=event.data.map(e => Object.assign({},e,{icon:apps.iconUrl(e.icon)}))
                    else if(event.type==="state")apps.state=Object.assign({},event.data,{groups:event.data.groups.map(g => Object.assign({},g,{icon:apps.iconUrl(g.icon)}))})
                    else if(event.type==="error") { apps.error=event.message;apps.busy=false }
                    else if(event.type==="done")apps.busy=false
                } catch(e) { apps.error="Не удалось прочитать список приложений";apps.busy=false }
            }
        }
        onExited: { apps.error="Служба приложений остановилась";apps.busy=false }
    }
    IpcHandler {
        target:"applications"
        function status():string { return JSON.stringify({entries:apps.entries.length,groups:apps.state.groups,workspaces:apps.state.workspaces,error:apps.error,busy:apps.busy,panel:apps.shell.openPanel,screen:apps.shell.openScreen}) }
        function menu():void { apps.toggle("launcher",apps.shell.osdScreen) }
        function windows(group:string):void { apps.toggle("applications",apps.shell.osdScreen,group==="-"?"":group) }
        function act(action:string,value:string):void { apps.act(action,["focus","close","fullscreen","maximize"].includes(action)?Number(value):value) }
    }
}
