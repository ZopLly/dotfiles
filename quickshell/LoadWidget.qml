pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: load
    required property var shell
    property var metrics: shell.dashboard.metrics
    property var samples: shell.dashboard.samples
    spacing: 8
    RowLayout {
        Layout.fillWidth: true
        Text { text: "󰻠"; color: load.shell.colors.accent; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 20 }
        Text { text: "Система"; color: load.shell.colors.fg; font.pixelSize: 13; font.weight: Font.DemiBold; Layout.fillWidth: true }
        Text { text: "CPU / RAM"; color: load.shell.colors.fg_dim; font.pixelSize: 10 }
    }
    RowLayout {
        Layout.fillWidth: true
        Repeater {
            model: [{field:"cpu", label:"Процессор"}, {field:"memory", label:"Память"}]
            ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: 5
                Text { text: modelData.label; color: load.shell.colors.fg_dim; font.pixelSize: 10 }
                Text {
                    objectName: "load-value-" + modelData.field
                    property var reading: load.metrics[modelData.field]
                    text: typeof reading === "number" && isFinite(reading) ? Math.round(reading)+"%" : "—"
                    color: load.shell.colors.fg; font.pixelSize: 24; font.weight: Font.Medium
                }
                Rectangle {
                    Layout.fillWidth: true; height: 4; radius: 2; color: Qt.alpha(load.shell.colors.accent, .12)
                    Rectangle {
                        width: parent.width * Math.max(0, Math.min(100, Number(load.metrics[modelData.field]) || 0))/100
                        height: parent.height; radius: 2; color: load.shell.colors.accent
                        Behavior on width { NumberAnimation { duration: 250 } }
                    }
                }
            }
        }
    }
    MetricGraph { shell: load.shell; samples: load.samples; Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 14; implicitHeight: 28 }
}
