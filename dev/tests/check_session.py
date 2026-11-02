#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('session_manager', Path(__file__).resolve().parents[2]/'session/session-manager.py')
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)

class SessionTests(unittest.TestCase):
    def test_capture_filters_apps_and_maps_workspaces(self):
        def query(kind):
            if kind == 'workspaces':
                return [dict(id=42, idx=2, name=None, output='eDP-1')]
            return [dict(id=i, app_id=app, workspace_id=42, layout={'pos_in_scrolling_layout': [3, 1] if i else None}) for i, app in enumerate(['Alacritty', 'firefox', 'Spotify', 'unknown'])]
        with patch.object(manager, 'query', side_effect=query):
            data = manager.capture()
        self.assertEqual(len(data['windows']), 3)
        self.assertTrue(all(w['workspace'] == '2' for w in data['windows']))
        self.assertIsNone(data['windows'][0]['column'])

    def test_atomic_private_snapshot(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(manager, 'STATE', Path(temp)):
            manager.save({'version': 2, 'windows': []})
            file = Path(temp)/'session.json'
            self.assertEqual(json.loads(file.read_text())['version'], 2)
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
            self.assertFalse((Path(temp)/'session.tmp').exists())

    def test_restore_reuses_existing_window_and_ignores_unknown_app(self):
        def query(kind):
            return [dict(id=7, app_id='Spotify')] if kind == 'windows' else {'eDP-1': {}}
        with patch.object(manager, 'query', side_effect=query), patch.object(manager, 'call') as call:
            manager.restore({'windows': [dict(app_id='Spotify', workspace='2', output='eDP-1', column=1), dict(app_id='evil', workspace='1')]})
            calls = [c.args[0] for c in call.call_args_list]
            self.assertEqual(len(calls), 2)
            self.assertIn('--window-id', calls[1])
            self.assertEqual(calls[1][-1], '2')
            self.assertTrue(all('spawn' not in c for c in calls))

    def test_restore_launches_only_allowlisted_commands(self):
        windows = iter([[], [dict(id=9, app_id='Alacritty')]])
        def query(kind):
            return next(windows) if kind == 'windows' else {}
        with patch.object(manager, 'query', side_effect=query), patch.object(manager, 'call') as call, patch.object(manager.STOP, 'wait', return_value=False):
            manager.restore({'windows': [dict(app_id='Alacritty', workspace='3', column=None)]})
            self.assertEqual(call.call_args_list[0].args[0], ['niri', 'msg', 'action', 'spawn', '--', 'alacritty'])
            self.assertEqual(call.call_args_list[-1].args[0][-3:], ['move-window-to-floating', '--id', '9'])

    def test_shutdown_freezes_saving(self):
        class Monitor:
            stdout = ['org.freedesktop.login1.Manager.PrepareForShutdown (true,)']
        try:
            manager.watch_shutdown(Monitor())
            self.assertTrue(manager.SHUTTING_DOWN.is_set())
            Monitor.stdout = ["org.freedesktop.login1.Manager.PrepareForShutdown (false,)"]
            manager.watch_shutdown(Monitor())
            self.assertFalse(manager.SHUTTING_DOWN.is_set())
        finally:
            manager.SHUTTING_DOWN.clear()

if __name__ == '__main__':
    unittest.main()
