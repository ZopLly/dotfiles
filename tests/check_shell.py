#!/usr/bin/env python3
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('shell_backend', ROOT/'quickshell/backend.py')
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)

class ShellTests(unittest.TestCase):
    def test_panel_layout_roundtrip_and_independence(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(backend, 'STATE', Path(temp)/'widgets.json'):
            backend.save_widget(dict(output='eDP-1', id='clock', x=.4))
            backend.action(dict(action='save-panel', args=dict(panel='center', modules=['media', 'calendar', 'audio'])))
            backend.save_panel(dict(panel='right', modules=[]))
            self.assertEqual(backend.panel_layouts(), dict(center=['media', 'calendar', 'audio'], right=[]))
            self.assertEqual(backend.layout_load()['eDP-1']['workspaces']['index:1']['clock']['x'], .4)
            backend.save_widget(dict(output='eDP-1', id='clock', visible=False))
            self.assertEqual(backend.panel_layouts()['right'], [])
            for values in (['media', 'media'], ['bad'], [dict(id='media')], 'media'):
                with self.assertRaises(ValueError): backend.save_panel(dict(panel='center', modules=values))
            self.assertEqual(backend.panel_layouts()['center'], ['media', 'calendar', 'audio'])

    def test_panel_defaults_and_invalid_saved_data(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(backend, 'STATE', Path(temp)/'widgets.json'):
            self.assertEqual(backend.panel_layouts(), backend.PANEL_DEFAULTS)
            backend.STATE.write_text(json.dumps({'_version': 2, '_panels': {'center': ['bad'], 'right': []}}))
            self.assertEqual(backend.panel_layouts(), dict(center=['calendar', 'media'], right=[]))

    def test_position_roundtrip_and_bounds(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(backend, 'STATE', Path(temp)/'widgets.json'):
            backend.save_widget(dict(output='eDP-1', id='clock', x=.35, y=.6, width=380, height=200))
            backend.save_widget(dict(output='HDMI-A-1', id='media', x=-10, y=30, width=900, height=1))
            result = backend.layout_load()
            self.assertEqual(result['eDP-1']['workspaces']['index:1']['clock']['x'], .35)
            self.assertEqual(result['HDMI-A-1']['workspaces']['index:1']['media'], dict(x=0, y=1, width=520, height=150, visible=True))
            with self.assertRaises(ValueError): backend.save_widget(dict(output='eDP-1', id='../bad', x=0, y=0))
            backend.action(dict(action='grid', args=dict(enabled=False)))
            self.assertFalse(backend.layout_load()['_options']['snap'])
            self.assertEqual(backend.layout_load()['eDP-1']['workspaces']['index:1']['clock']['width'], 380)

    def test_workspaces_are_independent_and_visibility_preserves_position(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(backend, 'STATE', Path(temp)/'widgets.json'):
            backend.save_widget(dict(output='eDP-1', workspace='index:1', id='clock', x=.2, y=.3))
            backend.save_widget(dict(output='eDP-1', workspace='index:2', id='clock', x=.8, y=.7))
            backend.save_widget(dict(output='eDP-1', workspace='index:2', id='clock', visible=False))
            data=backend.layout_load()['eDP-1']['workspaces']
            self.assertEqual(data['index:1']['clock']['x'], .2)
            self.assertTrue(data['index:1']['clock']['visible'])
            self.assertEqual(data['index:2']['clock']['x'], .8)
            self.assertFalse(data['index:2']['clock']['visible'])

    def test_legacy_positions_migrate_to_first_workspace(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(backend, 'STATE', Path(temp)/'widgets.json'):
            backend.STATE.write_text(json.dumps({'eDP-1': {'clock': {'x': .4, 'y': .5}}, '_options': {'snap': False}}))
            data=backend.layout_load()
            self.assertEqual(data['eDP-1']['workspaces']['index:1']['clock']['x'], .4)
            self.assertFalse(data['_options']['snap'])
            self.assertEqual(data['_version'], 2)

    def test_preview_blocks_all_system_controls(self):
        with patch.object(backend, 'PREVIEW', True), patch.object(backend, 'run') as run:
            for action in ('wifi', 'bluetooth', 'vpn', 'poweroff', 'reboot', 'suspend', 'lock', 'volume', 'brightness', 'dnd'):
                with self.assertRaises(RuntimeError): backend.action(dict(action=action))
            run.assert_not_called()

    def test_power_profiles_accept_string_values(self):
        with patch.object(backend, "PREVIEW", False), patch.object(backend, "run") as run:
            for profile in ("power-saver", "balanced", "performance"):
                backend.action(dict(action="profile", args=dict(value=profile)))
                self.assertEqual(run.call_args.args[0], ["powerprofilesctl", "set", profile])
            run.reset_mock()
            with self.assertRaises(ValueError):
                backend.action(dict(action="profile", args=dict(value="invalid")))
            run.assert_not_called()

    def test_volume_limits_and_valid_vpn(self):
        with patch.object(backend, 'PREVIEW', False), patch.object(backend, 'run') as run:
            backend.action(dict(action='volume', args=dict(value=350)))
            self.assertEqual(run.call_args.args[0][-1], '100%')
            backend.action(dict(action='brightness', args=dict(value=-8)))
            self.assertEqual(run.call_args.args[0][-1], '5%')
            with self.assertRaises(ValueError): backend.action(dict(action='vpn', args=dict(uuid='; evil')))
            uuid='12345678-1234-1234-1234-123456789abc'
            backend.action(dict(action='vpn', args=dict(uuid=uuid, enabled=True)))
            self.assertEqual(run.call_args.args[0], ['nmcli','connection','up','uuid',uuid])

    def test_snapshot_handles_missing_services_and_colon_names(self):
        uuid='12345678-1234-1234-1234-123456789abc'
        def optional(args, default=''):
            if 'workspaces' in args: return '[{"idx":2,"output":"eDP-1"},{"idx":1,"output":"eDP-1"}]'
            if 'keyboard-layouts' in args: return '{"names":["English (US)","Russian"],"current_idx":1}'
            if 'focused-window' in args: return 'null'
            if 'nmcli' == args[0] and 'connection' in args: return 'Office:VPN:vpn:'+uuid
            return default
        with patch.object(backend, 'PREVIEW', False), patch.object(backend, 'CACHE', backend.StateCache()), patch.object(backend, 'optional', side_effect=optional):
            state = backend.snapshot()
            self.assertEqual(state['vpns'][0]['name'], 'Office:VPN')
            self.assertTrue(state['vpns'][0]['active'])
            self.assertEqual(state['volume'], -1)
            self.assertEqual(state['workspaces'][0]['idx'], 1)
            self.assertEqual(state['language'], 'Russian')

    def test_malformed_layout_recovers(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(backend, 'STATE', Path(temp)/'widgets.json'):
            backend.STATE.write_text('invalid json')
            self.assertEqual(backend.layout_load(), {})

if __name__ == '__main__': unittest.main()
