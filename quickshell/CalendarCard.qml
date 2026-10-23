pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: calendar
    required property var shell
    property date displayed: new Date()
    property date selectedDate: new Date()
    property var agenda: shell.calendarState || ({configured: false, events: []})
    function dateKey(date) { return Qt.formatDate(date, "yyyy-MM-dd") }
    property bool outsideRange: !!agenda.rangeStart && (dateKey(selectedDate) < agenda.rangeStart || dateKey(selectedDate) > agenda.rangeEnd)
    property var selectedEvents: (agenda.events || []).filter(event => event.date === dateKey(selectedDate))
    property int firstDay: (new Date(displayed.getFullYear(), displayed.getMonth(), 1).getDay() + 6) % 7
    property int dayCount: new Date(displayed.getFullYear(), displayed.getMonth()+1, 0).getDate()
    spacing: 8
    function shift(amount) { displayed = new Date(displayed.getFullYear(), displayed.getMonth()+amount, 1); selectedDate = displayed }
    RowLayout {
        Layout.fillWidth: true
        ActionButton { shell: calendar.shell; text: "‹"; onClicked: calendar.shift(-1) }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: Qt.locale("ru_RU").standaloneMonthName(calendar.displayed.getMonth()) + " " + calendar.displayed.getFullYear()
            color: calendar.shell.colors.fg
            font.pixelSize: 16
        }
        ActionButton { shell: calendar.shell; text: "›"; onClicked: calendar.shift(1) }
    }
    GridLayout {
        Layout.fillWidth: true
        columns: 7
        columnSpacing: 3
        rowSpacing: 3
        Repeater {
            model: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            Text { required property string modelData; text: modelData; color: calendar.shell.colors.fg_dim; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; font.pixelSize: 12 }
        }
        Repeater {
            model: 7*Math.ceil((calendar.firstDay+calendar.dayCount)/7)
            Rectangle {
                required property int index
                property int day: index-calendar.firstDay+1
                property bool validDay: day>0 && day<=calendar.dayCount
                property bool today: validDay && day===calendar.shell.now.getDate() && calendar.displayed.getMonth()===calendar.shell.now.getMonth() && calendar.displayed.getFullYear()===calendar.shell.now.getFullYear()
                property bool selected: validDay && day === calendar.selectedDate.getDate() && calendar.displayed.getMonth() === calendar.selectedDate.getMonth() && calendar.displayed.getFullYear() === calendar.selectedDate.getFullYear()
                property bool hasEvents: validDay && (calendar.agenda.events || []).some(event => event.date === calendar.dateKey(new Date(calendar.displayed.getFullYear(), calendar.displayed.getMonth(), day)))
                border.width: selected ? 1 : 0
                border.color: calendar.shell.colors.accent
                Layout.fillWidth: true
                implicitHeight: 32
                radius: 12
                color: today ? calendar.shell.colors.accent : "transparent"
                Rectangle { width: 4; height: 4; radius: 2; anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 2; visible: parent.hasEvents; color: parent.today ? calendar.shell.colors.bg : (calendar.shell.colors.clock_color || calendar.shell.colors.accent) }
                MouseArea { anchors.fill: parent; enabled: parent.validDay; cursorShape: Qt.PointingHandCursor; onClicked: calendar.selectedDate = new Date(calendar.displayed.getFullYear(), calendar.displayed.getMonth(), parent.day) }
                Text { anchors.centerIn: parent; text: parent.validDay ? parent.day : ""; color: parent.today ? calendar.shell.colors.bg : calendar.shell.colors.fg; font.pixelSize: 13 }
            }
        }
    }
    ActionButton { shell: calendar.shell; text: "Сегодня"; Layout.alignment: Qt.AlignHCenter; quiet: true; onClicked: { calendar.displayed = new Date(); calendar.selectedDate = calendar.displayed } }
    Text {
        Layout.fillWidth: true
        text: calendar.selectedDate.toLocaleDateString(Qt.locale("ru_RU"), "d MMMM") + (calendar.agenda.preview ? " · пример событий" : "")
        color: calendar.shell.colors.fg; font.pixelSize: 14
    }
    Text {
        visible: !calendar.selectedEvents.length || !!calendar.agenda.error
        Layout.fillWidth: true; wrapMode: Text.Wrap
        text: calendar.agenda.error || (calendar.outsideRange ? "За пределами загруженного периода" : calendar.agenda.configured ? "Нет событий" : "Источник событий ещё не подключён")
        color: calendar.shell.colors.fg_dim; font.pixelSize: 12
    }
    Text { visible: !!calendar.agenda.updated; text: "Google Calendar · обновлено " + (calendar.agenda.updated || ""); color: calendar.shell.colors.fg_dim; font.pixelSize: 10; Layout.fillWidth: true; wrapMode: Text.Wrap }
    Repeater {
        model: calendar.selectedEvents
        ColumnLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: 3
            Text { text: parent.modelData.allDay ? "Весь день" : parent.modelData.time; color: calendar.shell.colors.accent; font.pixelSize: 11 }
            Text { text: parent.modelData.title || "Без названия"; textFormat: Text.PlainText; color: calendar.shell.colors.fg; font.pixelSize: 13; wrapMode: Text.Wrap; Layout.fillWidth: true }
        }
    }
}
