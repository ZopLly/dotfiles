#!/usr/bin/env python3
import sys
from pathlib import Path
import unittest
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quickshell'))
import backend
from system_state import bluetooth_state,wifi_state

class ConnectivityTests(unittest.TestCase):
    def test_known_found_and_connected_are_separate(self):
        def read(cmd,default=''):
            if cmd[-1]=='show':return 'Controller 00:11:22:33:44:55\nPowered: yes'
            if cmd[-1]=='Paired':return 'Device 00:11:22:33:44:01 Headset\nDevice 00:11:22:33:44:02 Mouse'
            if cmd[-1]=='Connected':return 'Device 00:11:22:33:44:01 Headset'
            return 'Device 00:11:22:33:44:01 Headset\nDevice 00:11:22:33:44:02 Mouse\nDevice 00:11:22:33:44:03 Keyboard'
        rows=bluetooth_state(read)['bluetooth_devices']
        self.assertEqual([(r['paired'],r['connected']) for r in rows],[(True,True),(True,False),(False,False)])

    def test_scan_is_async_and_does_not_hold_volume_controls(self):
        proc=MagicMock();proc.poll.return_value=None;proc.communicate.return_value=(b'',b'');proc.returncode=0
        with patch.object(backend,'PREVIEW',False),patch.object(backend,'TASKS',{}),patch.object(backend,'OPERATIONS',{}),patch.object(backend.subprocess,'Popen',return_value=proc) as spawn,patch.object(backend,'run') as run:
            backend.action({'action':'bluetooth-scan'})
            spawn.assert_called_once()
            self.assertTrue(backend.operation_state()['bluetooth']['busy'])
            backend.action({'action':'volume','args':{'value':44}})
            run.assert_called_once_with(['wpctl','set-volume','@DEFAULT_AUDIO_SINK@','44%'])
            proc.wait.assert_not_called()
            with self.assertRaises(RuntimeError):backend.action({'action':'bluetooth-scan'})
            proc.poll.return_value=0
            self.assertTrue(backend.poll_tasks())
            self.assertFalse(backend.operation_state()['bluetooth']['busy'])
            self.assertFalse(backend.TASKS)

    def test_pair_does_not_repeat_existing_pairing(self):
        with patch.object(backend,'PREVIEW',False),patch.object(backend,'bluetooth_state',return_value={'bluetooth_devices':[{'address':'00:11:22:33:44:01','paired':True}]}),patch.object(backend.subprocess,'Popen') as spawn:
            with self.assertRaises(ValueError):backend.action({'action':'bluetooth-pair','args':{'address':'00:11:22:33:44:01'}})
            spawn.assert_not_called()

    def test_wifi_connecting_state(self):
        def read(cmd,default=''):
            if cmd[-1]=='wifi':return 'enabled'
            if cmd[-1]=='device':return 'wlan0:wifi:connecting (configuring)'
            return ''
        result=wifi_state(read)
        self.assertEqual(result['wifi_connection_state'],'connecting')
        self.assertEqual(result['wifi_device'],'wlan0')
        self.assertFalse(result['wifi_connected'])

unittest.main()
