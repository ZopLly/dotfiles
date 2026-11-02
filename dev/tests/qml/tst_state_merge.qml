import QtQuick
import QtTest
import "../../../quickshell/StateMerge.js" as Merge
TestCase {
    name: "StableStateModels"
    function test_unrelated_volume_keeps_widget_and_model_references() {
        let original = {volume: 44, widgets: {screen: {clock: {x: 0.4}}}, colors: {bg: "#123456"}, workspaces: [{idx: 1}], sinks: [{name: "speaker"}]}
        let incoming = JSON.parse(JSON.stringify(original))
        incoming.volume = 45
        let result = Merge.retainEqual(original, incoming)
        verify(result.widgets === original.widgets)
        verify(result.colors === original.colors)
        verify(result.workspaces === original.workspaces)
        verify(result.sinks === original.sinks)
        compare(result.volume, 45)
    }
    function test_real_change_replaces_only_changed_model() {
        let original = {widgets: {clock: {x: 0.4}}, workspaces: [{idx: 1}]}
        let incoming = {widgets: {clock: {x: 0.5}}, workspaces: [{idx: 1}]}
        let result = Merge.retainEqual(original, incoming)
        verify(result.widgets !== original.widgets)
        verify(result.workspaces === original.workspaces)
        compare(result.widgets.clock.x, 0.5)
    }
    function test_binding_does_not_emit_for_equal_widget_model() {
        let subject = Qt.createQmlObject('import QtQuick; QtObject { property var state: ({widgets: {x: 0.4}}); property var widgets: state.widgets; property int changes: 0; onWidgetsChanged: changes += 1 }', this)
        let before = subject.changes
        subject.state = Merge.retainEqual(subject.state, {widgets: {x: 0.4}, volume: 45})
        compare(subject.changes, before)
        subject.state = Merge.retainEqual(subject.state, {widgets: {x: 0.5}, volume: 45})
        compare(subject.changes, before+1)
        subject.destroy()
    }
}
