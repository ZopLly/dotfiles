pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
Slider {
    id: slider
    required property var shell
    implicitHeight: 32
    background: Rectangle {
        x: slider.leftPadding
        y: slider.topPadding+(slider.availableHeight-height)/2
        width: slider.availableWidth; height: 7; radius: 4
        color: slider.shell.colors.fg_dim
        opacity: slider.enabled ? 0.7 : 0.3
        Rectangle { width: slider.visualPosition*parent.width; height: parent.height; radius: 4; color: slider.shell.colors.accent }
    }
    handle: Rectangle {
        x: slider.leftPadding+slider.visualPosition*(slider.availableWidth-width)
        y: slider.topPadding+(slider.availableHeight-height)/2
        width: 16; height: 16; radius: 8
        color: slider.shell.colors.fg
        opacity: slider.enabled ? 1 : 0.4
    }
}
