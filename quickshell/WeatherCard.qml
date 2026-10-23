pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: weather
    required property var shell
    property bool compact: false
    property bool expanded: false
    property var report: shell.weather || {}
    spacing: compact ? 4 : 10
    function condition(code) {
        if (code === undefined) return ""
        if (code === 0) return "Ясно"
        if (code <= 3) return "Облачно"
        if (code === 45 || code === 48) return "Туман"
        if (code >= 95) return "Гроза"
        if ((code >= 71 && code <= 77) || code === 85 || code === 86) return "Снег"
        if (code >= 51 && code <= 67 || code >= 80 && code <= 82) return "Дождь"
        return "Переменная погода"
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        Rectangle {
            Layout.preferredWidth: weather.compact ? 44 : 52; Layout.preferredHeight: Layout.preferredWidth
            radius: 15; color: Qt.alpha(weather.shell.colors.accent, .12)
            Text { anchors.centerIn: parent; text: weather.report.code === 0 ? "☀" : weather.report.code >= 51 ? "☂" : "☁"; font.pixelSize: 26; color: weather.shell.colors.accent }
        }
        ColumnLayout {
            Layout.fillWidth: true; spacing: 2
            Text { text: "Москва"; color: weather.shell.colors.fg_dim; font.pixelSize: 11 }
            Text { text: weather.report.temperature === undefined ? "—" : weather.report.temperature+"°C"; color: weather.shell.colors.fg; font.pixelSize: weather.compact ? 24 : 28; font.weight: Font.Medium }
        }
    }
    Text { text: weather.report.temperature === undefined ? (weather.report.error ? "Погода недоступна · проверь сеть" : "Ожидание погоды…") : weather.condition(weather.report.code) + " · ощущается " + weather.report.feels + "°"; color: weather.shell.colors.fg_dim; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.Wrap }
    ActionButton { visible: !weather.compact; shell: weather.shell; Layout.fillWidth: true; text: weather.expanded ? "Скрыть прогноз" : "Прогноз на 3 дня"; onClicked: weather.expanded = !weather.expanded }
    Repeater {
        model: weather.expanded && !weather.compact ? (weather.report.days || []) : []
        delegate: Text {
            required property var modelData
            text: modelData.date.slice(8) + "." + modelData.date.slice(5,7) + "   " + modelData.low + "…" + modelData.high + "°  " + weather.condition(modelData.code)
            color: weather.shell.colors.fg; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.Wrap
        }
    }
    Text { text: weather.report.preview ? "Пример прогноза" : weather.report.error ? weather.report.error + (weather.report.updated ? " · " + weather.report.updated.replace("T", " ") : "") : weather.report.updated ? (weather.report.stale ? "Сохранено: " : "Данные: ") + weather.report.updated.replace("T", " ") : ""; color: weather.shell.colors.fg_dim; font.pixelSize: 10; Layout.fillWidth: true; wrapMode: Text.Wrap }
    Text { text: "Open-Meteo · CC BY 4.0"; color: weather.shell.colors.fg_dim; font.pixelSize: 10 }
}
