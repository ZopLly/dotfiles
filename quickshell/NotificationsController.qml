pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
Scope {
    id: controller
    property var state: ({available:false,active:[],history:[],dnd:false,error:""})
    function act(action,value) { backend.write(JSON.stringify({action:action,value:value})+"\n") }
    Process {
        id:backend
        command:["python3",Quickshell.shellDir+"/notifications.py"]
        running:true;stdinEnabled:true
        stdout:SplitParser { onRead:data => {
            try { controller.state=JSON.parse(data) }
            catch(e) { console.warn("Invalid notification state") }
        } }
        onExited: if (controller.state.available) controller.state=({available:false,active:[],history:[],dnd:false,error:"Служба просмотра уведомлений остановилась"})
    }
}
