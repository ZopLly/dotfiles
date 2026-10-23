pragma ComponentBehavior: Bound
import QtQuick
import "StatusIcons.js" as Icons
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: control
    required property var shell
    required property string outputName
    property var navigator: null
    property bool detailed: false
    property var systemState: shell.state
    property string pendingPower: ""
    onVisibleChanged: if (!visible) pendingPower = ""
    spacing: 12
    Text { text: "Звук"; color: control.shell.colors.fg; font.pixelSize: 14 }
    RowLayout {
        Layout.fillWidth: true
        ActionButton { shell: control.shell; text: Icons.volume(control.systemState.volume, control.systemState.muted); enabled: !!control.systemState.available; onClicked: control.shell.send("mute") }
        ThemedSlider {
        shell: control.shell; Layout.fillWidth: true; from: 0; to: 100; value: Math.max(0, control.systemState.volume || 0); enabled: !!control.systemState.available && control.systemState.volume >= 0; onMoved: control.shell.send("volume", {value: Math.round(value)}) }
        Text { text: (control.systemState.volume >= 0 ? control.systemState.volume : "—") + "%"; color: control.shell.colors.fg }
    }
    ThemedChoice {
        visible: control.detailed
        shell: control.shell; Layout.fillWidth: true
        property var devices: control.systemState.sinks || []
        model: devices.map(d => d.label)
        currentIndex: devices.findIndex(d => d.active)
        enabled: !!control.systemState.available && devices.length > 0
        onActivated: control.shell.send("audio-sink", {name: devices[currentIndex].name})
    }
    RowLayout {
        visible: control.detailed
        Layout.fillWidth: true
        ActionButton { shell: control.shell; text: control.systemState.mic_muted ? "󰍭" : "󰍬"; enabled: !!control.systemState.available && control.systemState.mic_volume >= 0; onClicked: control.shell.send("mic-mute") }
        ThemedSlider { shell: control.shell; Layout.fillWidth: true; from: 0; to: 100; value: Math.max(0, control.systemState.mic_volume || 0); enabled: !!control.systemState.available && control.systemState.mic_volume >= 0; onMoved: control.shell.send("mic-volume", {value: Math.round(value)}) }
        Text { text: control.systemState.mic_volume >= 0 ? control.systemState.mic_volume + "%" : "—"; color: control.shell.colors.fg }
    }
    ThemedChoice {
        visible: control.detailed
        shell: control.shell; Layout.fillWidth: true
        property var devices: control.systemState.sources || []
        model: devices.map(d => d.label)
        currentIndex: devices.findIndex(d => d.active)
        enabled: !!control.systemState.available && devices.length > 0
        onActivated: control.shell.send("audio-source", {name: devices[currentIndex].name})
    }
    ActionButton { visible: control.detailed; shell: control.shell; text: "Устройства звука"; enabled: !!control.systemState.available; onClicked: control.shell.send("audio-settings") }
    ActionButton { visible: !control.detailed && !!control.navigator; shell: control.shell; Layout.fillWidth: true; text: "Устройства и микрофон ›"; onClicked: control.navigator.navigate("audio") }
}
