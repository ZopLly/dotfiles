pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id:dashboard
    required property var shell
    required property string outputName
    readonly property string currentTab:shell.dashboard.section
    property bool wide:width>=650
    property var metrics:shell.dashboard.metrics
    property var space:(shell.workspaces || []).find(w=>w.output===outputName && w.is_active) || ({})
    property var desktopWindows:windowsOnDesktop()
    function windowsOnDesktop() {
        let result=[]
        for (let group of shell.applications.state.groups || [])
            for (let win of group.windows || [])
                if (win.workspace_id===space.id) result.push(Object.assign({},win,{icon:group.icon}))
        return result
    }
    spacing:16
    function percent(value) {return typeof value==="number"?Math.round(value)+" %":"—"}
    function memoryText() {return metrics.memory_total?((metrics.memory_used/1073741824).toFixed(1)+" / "+(metrics.memory_total/1073741824).toFixed(1)+" ГБ"):"—"}
    function uptimeText() {return typeof metrics.uptime==="number"?Math.floor(metrics.uptime/3600)+" ч "+Math.floor(metrics.uptime%3600/60)+" мин":"—"}
    RowLayout {
        Layout.fillWidth:true
        ColumnLayout {
            Layout.fillWidth:true;spacing:4
            Text {text:"Твой рабочий стол";color:dashboard.shell.colors.fg;font.pixelSize:25;font.weight:Font.DemiBold}
            Text {text:"Всё важное рядом";color:dashboard.shell.colors.fg_dim;font.pixelSize:12}
        }
        ActionButton {shell:dashboard.shell;text:"󰏘";ToolTip.visible:hovered;ToolTip.text:"Темы и обои";onClicked:dashboard.shell.applications.act("settings",null)}
    }
    Flow {
        Layout.fillWidth:true;spacing:6
        Repeater {
            model:[{id:"overview",label:"Обзор"},{id:"media",label:"Медиа"},{id:"performance",label:"Производительность"},{id:"weather",label:"Погода"},{id:"modules",label:"Модули"}]
            ActionButton {
                required property var modelData
                shell:dashboard.shell;objectName:"dashboard-tab-"+modelData.id
                text:modelData.label;selected:dashboard.currentTab===modelData.id
                onClicked:dashboard.shell.dashboard.section=modelData.id
            }
        }
    }
    Loader {
        Layout.fillWidth:true;Layout.preferredHeight:item?item.implicitHeight:0
        sourceComponent:dashboard.currentTab==="overview"?overview:dashboard.currentTab==="media"?mediaPage:dashboard.currentTab==="performance"?performancePage:dashboard.currentTab==="weather"?weatherPage:modulesPage
    }
    Component {
        id:overview
        ColumnLayout {
            spacing:14
            GridLayout {
                Layout.fillWidth:true;columns:dashboard.wide?2:1;columnSpacing:14;rowSpacing:14
                DashboardTile {
                    shell:dashboard.shell;Layout.fillWidth:true;Layout.minimumWidth:0
                    RowLayout {
                        Layout.fillWidth:true
                        ColumnLayout {
                            Layout.fillWidth:true;spacing:4
                            Text {text:Qt.formatTime(dashboard.shell.now,"HH:mm");color:dashboard.shell.colors.fg;font.pixelSize:60;font.weight:Font.Light}
                            Text {text:dashboard.shell.now.toLocaleDateString(Qt.locale("ru_RU"),"dddd, d MMMM");color:dashboard.shell.colors.fg_dim;font.pixelSize:13}
                        }
                        Text {text:"◷";color:dashboard.shell.colors.accent;font.pixelSize:48}
                    }
                    Rectangle {Layout.fillWidth:true;implicitHeight:1;color:Qt.alpha(dashboard.shell.colors.fg,0.12)}
                    RowLayout {
                        Layout.fillWidth:true
                        Text {text:dashboard.space.name || "Стол "+(dashboard.space.idx || "—");color:dashboard.shell.colors.fg;font.pixelSize:12;Layout.fillWidth:true;elide:Text.ElideRight}
                        Text {text:dashboard.desktopWindows.length+" окон";color:dashboard.shell.colors.fg_dim;font.pixelSize:11}
                    }
                    RowLayout {
                        visible:dashboard.desktopWindows.length>0;Layout.fillWidth:true;spacing:6
                        Repeater {
                            model:dashboard.desktopWindows.slice(0,6)
                            ActionButton {
                                required property var modelData
                                shell:dashboard.shell;Layout.preferredWidth:36;Layout.preferredHeight:36
                                text:modelData.icon?"":"□";quiet:true
                                Image {anchors.centerIn:parent;width:18;height:18;source:parent.modelData.icon || "";asynchronous:true;fillMode:Image.PreserveAspectFit}
                                ToolTip.visible:hovered;ToolTip.text:modelData.title || "Окно"
                                onClicked:dashboard.shell.applications.act("focus",modelData.id)
                            }
                        }
                        Item {Layout.fillWidth:true}
                    }
                }
                DashboardTile {
                    shell:dashboard.shell;Layout.fillWidth:true;Layout.minimumWidth:0;title:"ПОГОДА"
                    WeatherCard {shell:dashboard.shell;compact:true;Layout.fillWidth:true}
                    ActionButton {shell:dashboard.shell;text:"Открыть прогноз  ↗";Layout.fillWidth:true;onClicked:dashboard.shell.dashboard.section="weather"}
                }
            }
            GridLayout {
                Layout.fillWidth:true;columns:dashboard.wide?2:1;columnSpacing:14;rowSpacing:14
                DashboardTile {
                    shell:dashboard.shell;Layout.fillWidth:true;Layout.minimumWidth:0;Layout.alignment:Qt.AlignTop;title:"КАЛЕНДАРЬ И ПОВЕСТКА"
                    CalendarCard {shell:dashboard.shell;Layout.fillWidth:true}
                }
                ColumnLayout {
                    Layout.fillWidth:true;Layout.minimumWidth:0;Layout.alignment:Qt.AlignTop;spacing:14
                    DashboardTile {
                        shell:dashboard.shell;Layout.fillWidth:true;title:"СЕЙЧАС ИГРАЕТ"
                        MediaCard {shell:dashboard.shell;Layout.fillWidth:true}
                    }
                    DashboardTile {
                        shell:dashboard.shell;Layout.fillWidth:true;title:"СОСТОЯНИЕ СИСТЕМЫ"
                        RowLayout {
                            Layout.fillWidth:true
                            MetricRing {shell:dashboard.shell;caption:"CPU";value:dashboard.metrics.cpu ?? null;Layout.fillWidth:true}
                            MetricRing {shell:dashboard.shell;caption:"Память";value:dashboard.metrics.memory ?? null;Layout.fillWidth:true}
                            MetricRing {shell:dashboard.shell;caption:"Батарея";value:dashboard.shell.state.battery && dashboard.shell.state.battery.percent>=0?dashboard.shell.state.battery.percent:null;Layout.fillWidth:true}
                        }
                        ActionButton {shell:dashboard.shell;text:"Производительность  ↗";Layout.fillWidth:true;onClicked:dashboard.shell.dashboard.section="performance"}
                    }
                }
            }
        }
    }
    Component {
        id:mediaPage
        DashboardTile {
            shell:dashboard.shell;title:"МЕДИА"
            MediaCard {shell:dashboard.shell;Layout.fillWidth:true}
        }
    }
    Component {
        id:weatherPage
        DashboardTile {
            shell:dashboard.shell;title:"ПОГОДА И ПРОГНОЗ"
            WeatherCard {shell:dashboard.shell;expanded:true;Layout.fillWidth:true}
        }
    }
    Component {
        id:performancePage
        ColumnLayout {
            spacing:14
            DashboardTile {
                shell:dashboard.shell;Layout.fillWidth:true;title:"ПРОЦЕССОР"
                RowLayout {
                    Layout.fillWidth:true
                    Text {text:dashboard.percent(dashboard.metrics.cpu);font.pixelSize:36;color:dashboard.shell.colors.fg;Layout.fillWidth:true}
                    Text {text:(dashboard.metrics.cores || "—")+" потоков";color:dashboard.shell.colors.fg_dim;font.pixelSize:12}
                }
                MetricGraph {shell:dashboard.shell;samples:dashboard.shell.dashboard.samples;field:"cpu";Layout.fillWidth:true}
                Text {text:"0–100 % · до трёх минут при открытом дашборде";color:dashboard.shell.colors.fg_dim;font.pixelSize:11;wrapMode:Text.Wrap;Layout.fillWidth:true}
            }
            DashboardTile {
                shell:dashboard.shell;Layout.fillWidth:true;title:"ОПЕРАТИВНАЯ ПАМЯТЬ"
                RowLayout {
                    Layout.fillWidth:true
                    Text {text:dashboard.percent(dashboard.metrics.memory);font.pixelSize:36;color:dashboard.shell.colors.fg;Layout.fillWidth:true}
                    Text {text:dashboard.memoryText();color:dashboard.shell.colors.fg_dim;font.pixelSize:12}
                }
                MetricGraph {shell:dashboard.shell;samples:dashboard.shell.dashboard.samples;field:"memory";Layout.fillWidth:true}
            }
            DashboardTile {
                shell:dashboard.shell;Layout.fillWidth:true;title:"СЕАНС"
                Text {text:"Время работы  ·  "+dashboard.uptimeText();color:dashboard.shell.colors.fg;font.pixelSize:13}
                Text {text:"Средняя нагрузка за минуту  ·  "+(dashboard.metrics.load ?? "—");color:dashboard.shell.colors.fg;font.pixelSize:13}
                Text {text:"Подкачка  ·  "+dashboard.percent(dashboard.metrics.swap);color:dashboard.shell.colors.fg;font.pixelSize:13}
                Text {visible:!!dashboard.shell.dashboard.error;text:dashboard.shell.dashboard.error;color:dashboard.shell.colors.power_color;font.pixelSize:12}
            }
        }
    }
    Component {id:modulesPage;PanelModules {shell:dashboard.shell;outputName:dashboard.outputName;panel:"center"}}
}
