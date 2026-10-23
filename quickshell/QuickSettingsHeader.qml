pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
 id:header
 required property var shell
 property string outputName:""
 property var activeWorkspace:(shell.applications.state?.workspaces || []).find(w => outputName?w.output===outputName && w.is_active:w.is_focused)
 property bool freeMode:!!activeWorkspace && !!(shell.applications.state?.window_modes || {})[String(activeWorkspace.id)]
 Layout.fillWidth:true;spacing:8
 RowLayout {
  Layout.fillWidth:true
  Text {text:"Быстрые настройки";font.pixelSize:17;font.bold:true;color:header.shell.colors.fg;Layout.fillWidth:true}
  ActionButton {objectName:"quick-appearance";shell:header.shell;text:"Оформление";onClicked:header.shell.applications.act("settings")}
 }
 ActionButton {
  objectName:"workspace-mode";shell:header.shell;Layout.fillWidth:true
  text:header.freeMode?"Вернуть тайлинг этого стола":"Свободные окна на этом столе"
  enabled:!header.shell.applications.busy
  onClicked:header.shell.applications.act("workspace-mode",header.outputName)
 }
}
