pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: media
    required property var shell
    property bool compact: false
    property var player: shell.player
    spacing: compact ? 8 : 10
    RowLayout {
        Layout.fillWidth: true
        Rectangle {
            Layout.preferredWidth: media.compact ? 48 : 70; Layout.preferredHeight: Layout.preferredWidth; radius: 14
            color: media.shell.colors.bg
            clip: true
            Image { anchors.fill: parent; source: media.player ? media.player.trackArtUrl : ""; fillMode: Image.PreserveAspectCrop; sourceSize.width: 140; sourceSize.height: 140; asynchronous: true }
            Text { anchors.centerIn: parent; visible: !media.player || !media.player.trackArtUrl; text: "♫"; font.pixelSize: 30; color: media.shell.colors.accent }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: media.player ? (media.player.trackTitle || "Без названия") : "Музыка не играет"; color: media.shell.colors.fg; font.pixelSize: 14; elide: Text.ElideRight }
            Text { Layout.fillWidth: true; text: media.player ? (media.player.trackArtist || media.player.identity) : "Открой Spotify или другой плеер"; color: media.shell.colors.fg_dim; font.pixelSize: 11; elide: Text.ElideRight }
        }
    }
    ThemedChoice { shell: media.shell;
        visible: !media.compact && media.shell.players.length > 1
        Layout.fillWidth: true
        model: media.shell.players.map(p => p.identity)
        onActivated: media.shell.playerIndex = currentIndex
    }
    ThemedSlider {
        shell: media.shell;
        visible: !media.compact && !!media.player && media.player.positionSupported && media.player.length > 0
        enabled: !!media.player && media.player.canSeek
        Layout.fillWidth: true
        from: 0; to: media.player ? Math.max(1, media.player.length) : 1
        value: media.player ? media.player.position : 0
        onMoved: if (media.player && media.player.canSeek) media.player.position = value
    }
    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        ActionButton { shell: media.shell; text: "󰒮"; enabled: !!media.player && media.player.canGoPrevious; onClicked: media.player.previous() }
        ActionButton { shell: media.shell; text: media.player && media.player.isPlaying ? "󰏤" : "󰐊"; selected: true; enabled: !!media.player && media.player.canTogglePlaying; onClicked: media.player.togglePlaying() }
        ActionButton { shell: media.shell; text: "󰒭"; enabled: !!media.player && media.player.canGoNext; onClicked: media.player.next() }
    }
    Loader {
        id:visualization
        Layout.fillWidth:true
        Layout.preferredHeight:media.compact ? 28 : 64
        visible:media.visible && (!media.compact || media.height >= 132) && !!media.player && media.player.isPlaying && !media.shell.state.preview
        active:visible
        function loadVisualizer() { if(active) setSource(Qt.resolvedUrl("AudioBars.qml"),{shell:media.shell,active:true});else source="" }
        onActiveChanged:loadVisualizer()
        Component.onCompleted:loadVisualizer()
    }
    Timer { interval: 1000; running: media.visible && !!media.player && media.player.isPlaying; repeat: true; onTriggered: media.player.positionChanged() }
}
