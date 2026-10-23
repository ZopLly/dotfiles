#!/usr/bin/env python3
"""Offline hardware regressions: no real radio, audio or service mutations."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'quickshell'))
import system_state as adapter
import backend

class SystemTests(unittest.TestCase):
    def test_wifi_escaped_ssid_signal_and_radio_states(self):
        def read(cmd, default=''):
            return 'enabled' if cmd[-1] == 'wifi' else r'*:Office\:AP:63:AA\:BB\:CC\:DD\:EE\:FF:WPA2'
        state = adapter.wifi_state(read)
        self.assertEqual(state['network'], 'Office:AP')
        self.assertEqual(state['wifi_signal'], 63)
        self.assertTrue(state['wifi_connected'])
        self.assertEqual(state['networks'][0]['bssid'], 'AA:BB:CC:DD:EE:FF')
        for radio, available in (('disabled', True), ('', False)):
            state = adapter.wifi_state(lambda cmd, default='': radio if cmd[-1] == 'wifi' else '')
            self.assertFalse(state['wifi_connected'])
            self.assertFalse(state['wifi'])
            self.assertEqual(state['wifi_available'], available)

    def test_audio_defaults_microphone_and_monitor_filter(self):
        def read(cmd, default=''):
            if cmd[0] == 'wpctl': return 'Volume: 0.44 [MUTED]' if 'SINK' in cmd[-1] else 'Volume: 0.65'
            if cmd[1].startswith('get-default-'): return 'bluez_output.headset' if cmd[1].endswith('sink') else 'mic'
            return json.dumps([{'name':'bluez_output.headset','description':'Headphones'}, {'name':'mic'}, {'name':'speaker.monitor'}])
        state = adapter.audio_state(read)
        self.assertEqual(state['volume'],44)
        self.assertEqual(state['mic_volume'],65)
        self.assertTrue(state['muted'])
        self.assertFalse(state['mic_muted'])
        self.assertTrue(state['sinks'][0]['active'])
        self.assertEqual(len(state['sources']),2)
        self.assertEqual(adapter.audio_state(lambda cmd, default='':default)['volume'],-1)

    def test_bluetooth_connected_and_unavailable(self):
        def read(cmd, default=''):
            return 'Controller AA:BB:CC:DD:EE:FF\n Powered: yes' if cmd[-1]=='show' else 'Device AA:BB:CC:DD:EE:01 Headphones'
        state = adapter.bluetooth_state(read)
        self.assertTrue(state['bluetooth_available'])
        self.assertTrue(state['bluetooth_devices'][0]['connected'])
        self.assertFalse(adapter.bluetooth_state(lambda cmd, default='':'')['bluetooth_available'])

    def test_battery_states_and_backlight_class(self):
        for percent, status, level in ((-1,'','unavailable'),(100,'Full','full'),(3,'Charging','charging'),(5,'Discharging','critical'),(15,'Discharging','low'),(70,'Discharging','discharging')):
            self.assertEqual(adapter.battery_level(percent,status),level)
        with patch('system_state.Path') as path:
            path.return_value.glob.return_value=[]
            self.assertEqual(adapter.backlight_signature(),())
        with patch.object(backend,'run',return_value='') as run, patch.object(backend,'PREVIEW',False):
            backend.action({'action':'brightness','args':{'value':50}})
            self.assertEqual(run.call_args.args[0],['brightnessctl','--class=backlight','set','50%'])

    def test_private_atomic_layout_backup_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(backend,'STATE',Path(tmp)/'widgets.json'):
            backend.STATE.write_text('{"eDP-1":{"clock":{"x":0.3,"width":400}}}')
            original=backend.STATE.read_bytes()
            backend.save_widget({'output':'eDP-1','id':'clock','visible':False})
            self.assertEqual(backend.STATE.with_suffix('.json.bak').read_bytes(),original)
            self.assertEqual(backend.STATE.stat().st_mode & 0o777,0o600)
            self.assertEqual(backend.layout_load()['eDP-1']['workspaces']['index:1']['clock']['width'],400)
            for value in (float('nan'),float('inf')):
                with self.assertRaises(ValueError):backend.save_widget({'output':'eDP-1','id':'clock','x':value})

    def test_metrics_widget_preserves_existing_layout(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(backend, 'STATE', Path(tmp)/'widgets.json'):
            backend.save_widget({'output':'eDP-1', 'id':'clock', 'x':.4, 'width':350})
            clock = backend.layout_load()['eDP-1']['workspaces']['index:1']['clock'].copy()
            backend.save_widget({'output':'eDP-1', 'id':'metrics', 'visible':True})
            widgets = backend.layout_load()['eDP-1']['workspaces']['index:1']
            self.assertEqual(widgets['clock'], clock)
            self.assertTrue(widgets['metrics']['visible'])
            backend.save_widget({'output':'eDP-1', 'id':'metrics', 'visible':False})
            self.assertFalse(backend.layout_load()['eDP-1']['workspaces']['index:1']['metrics']['visible'])

    def test_actions_validate_and_preview_blocks_new_controls(self):
        with patch.object(backend,'PREVIEW',True),patch.object(backend,'run') as run,patch.object(backend.subprocess,'Popen') as popen:
            for action in ('wifi-connect','wifi-disconnect','wifi-rescan','bluetooth-device','bluetooth-scan','bluetooth-pair','audio-sink','audio-source','mic-volume','mic-mute'):
                with self.assertRaises(RuntimeError):backend.action({'action':action})
            run.assert_not_called();popen.assert_not_called()
        with patch.object(backend,'PREVIEW',False),patch.object(backend,'TASKS',{}),patch.object(backend,'OPERATIONS',{}),patch.object(backend,'run') as run,patch.object(backend.subprocess,'Popen') as popen:
            for action,args in (('wifi-connect',{'bssid':'bad'}),('bluetooth-device',{'address':'bad'}),('audio-sink',{'name':'bad'})):
                with patch.object(backend,'optional',return_value=''):
                    with self.assertRaises(ValueError):backend.action({'action':action,'args':args})
            run.assert_not_called();popen.assert_not_called()
            backend.action({'action':'wifi-connect','args':{'bssid':'AA:BB:CC:DD:EE:FF'}})
            self.assertEqual(popen.call_args.args[0],['alacritty','-e','bash',str(backend.ROOT/'quickshell/wifi-connect.sh'),'AA:BB:CC:DD:EE:FF'])

    def test_bridge_process_with_isolated_preview_and_eof(self):
        with tempfile.TemporaryDirectory() as tmp:
            env=dict(os.environ,NIRI_SHELL_PREVIEW='1',XDG_STATE_HOME=tmp,NIRI_SOCKET='/tmp/nonexistent-odyssey-socket')
            proc=subprocess.run([sys.executable,str(ROOT/'quickshell/backend.py')],input=json.dumps({'action':'save-widget','args':{'output':'test','id':'weather','x':.7}})+'\n',text=True,capture_output=True,env=env,timeout=5)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertEqual(json.loads(proc.stdout.splitlines()[0])['type'],'state')
            saved=json.loads((Path(tmp)/'niri-shell/widgets.json').read_text())
            self.assertEqual(saved['test']['workspaces']['index:1']['weather']['x'],.7)

if __name__=='__main__':unittest.main()
