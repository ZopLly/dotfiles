#!/usr/bin/env python3
"""Behavior at the desktop metadata / Niri boundary, with no live IPC."""
import importlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'quickshell'))
ENTRIES = [
    dict(id='firefox.desktop', name='Firefox', icon='firefox', aliases=['firefox', 'Navigator']),
    dict(id='Alacritty.desktop', name='Alacritty', icon='Alacritty', aliases=['Alacritty']),
    dict(id='one.desktop', name='One', icon='', aliases=['electron']),
    dict(id='two.desktop', name='Two', icon='', aliases=['electron']),
]
WORKSPACES = [dict(id=42, idx=1, output='winit', is_active=True), dict(id=99, idx=2, output='winit', is_active=False)]
WINDOWS = [dict(id=900, app_id='firefox', title='Web', workspace_id=99, is_focused=False, is_floating=False, is_urgent=True),
           dict(id=12, app_id='Navigator', title='Docs', workspace_id=42, is_focused=True, is_floating=False, is_urgent=False),
           dict(id=0, app_id='electron', title='Unknown', workspace_id=42, is_focused=False, is_floating=True, is_urgent=False)]

class ApplicationTests(unittest.TestCase):
    def model(self):
        self.assertTrue((ROOT/'quickshell/applications/model.py').exists(), 'Application grouping not implemented')
        return importlib.import_module('applications.model')

    def test_same_app_group_retains_window_ids_and_focus(self):
        result = self.model().groups(ENTRIES, WINDOWS, WORKSPACES)
        fox = next(g for g in result if g['id']=='firefox.desktop')
        self.assertEqual([w['id'] for w in fox['windows']], [12, 900])
        self.assertTrue(fox['active']); self.assertTrue(fox['urgent'])
        self.assertEqual(fox['windows'][1]['workspace_label'], '2')

    def test_ambiguous_startup_class_stays_unknown(self):
        unknown = next(g for g in self.model().groups(ENTRIES, WINDOWS, WORKSPACES) if g['windows'][0]['id']==0)
        self.assertIsNone(unknown['desktop_id'])
        self.assertEqual(unknown['id'], 'window-app:electron')

    def test_filter_uses_workspace_id_and_output(self):
        result = self.model().groups(ENTRIES, WINDOWS, WORKSPACES, current_only=True, output='winit')
        self.assertEqual(sorted(w['id'] for g in result for w in g['windows']), [0, 12])
        self.assertEqual(self.model().groups(ENTRIES, WINDOWS, WORKSPACES, current_only=True, output='absent'), [])

    def test_no_app_id_windows_do_not_collapse_into_one_group(self):
        windows = [dict(WINDOWS[0], id=7, app_id=None), dict(WINDOWS[0], id=8, app_id=None)]
        self.assertEqual(len(self.model().groups(ENTRIES, windows, WORKSPACES)), 2)

    def test_desktop_id_wins_over_another_entries_alias(self):
        entries=ENTRIES+[dict(id='custom.desktop',name='Custom',icon='',aliases=['firefox'])]
        group=self.model().groups(entries,[WINDOWS[0]],WORKSPACES)[0]
        self.assertEqual(group['desktop_id'],'firefox.desktop')

    def test_case_distinct_desktop_ids_match_exactly_without_overwriting(self):
        entries=[dict(id='Foo.desktop',name='Upper',icon='',aliases=['Foo']),dict(id='foo.desktop',name='Lower',icon='',aliases=['foo'])]
        windows=[dict(WINDOWS[0],id=1,app_id='Foo'),dict(WINDOWS[0],id=2,app_id='foo'),dict(WINDOWS[0],id=3,app_id='FOO')]
        result=self.model().groups(entries,windows,WORKSPACES)
        identities={w['id']:g['desktop_id'] for g in result for w in g['windows']}
        self.assertEqual(identities,{1:'Foo.desktop',2:'foo.desktop',3:None})

    def test_gio_catalogue_contains_installed_apps_without_commands(self):
        entries=self.model().desktop_entries()
        self.assertIn('Alacritty.desktop',[e['id'] for e in entries])
        self.assertTrue(all(set(e)=={'id','name','icon','aliases'} for e in entries))
        self.assertEqual(len({e['id'] for e in entries}),len(entries))

    def test_snapshot_tracks_actual_focus_not_fixed_favorites(self):
        from applications.service import ApplicationService
        from subprocess import CompletedProcess
        entries=ENTRIES+[dict(id='chatgpt.desktop',name='ChatGPT',icon='',aliases=['chatgpt'])]
        window=dict(id=1,app_id='firefox',title='private document title',workspace_id=42,is_focused=True,is_floating=False,is_urgent=False)
        def runner(args,**kwargs):
            data=[window] if args[-1]=='windows' else WORKSPACES
            return CompletedProcess(args,0,stdout=json.dumps(data),stderr='')
        with tempfile.TemporaryDirectory() as temp,patch('applications.service.session_enabled',return_value=True):
            state=Path(temp);service=ApplicationService(state,state,entries,False,runner=runner)
            self.assertEqual(service.snapshot()['usage'],{'firefox.desktop':1})
            self.assertEqual(service.snapshot()['usage'],{'firefox.desktop':1})
            window['app_id']='chatgpt'
            self.assertEqual(service.snapshot()['usage'],{'firefox.desktop':1,'chatgpt.desktop':1})
            window['is_focused']=False;service.snapshot()
            window['is_focused']=True;service.snapshot()
            self.assertEqual(service.snapshot()['usage']['chatgpt.desktop'],1)
            window['app_id']='firefox';self.assertEqual(service.snapshot()['usage']['firefox.desktop'],2)
            self.assertNotIn('private document title',(state/'application-usage.json').read_text())
            with patch.object(service.usage,'observe',side_effect=PermissionError('unwritable')):
                self.assertTrue(service.snapshot()['groups'])

    def test_settings_show_escapes_cli_subcommands(self):
        from applications.service import ApplicationService
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);commands=[]
            def runner(args,**kwargs):
                import subprocess
                commands.append(args)
                return subprocess.CompletedProcess(args,0,stdout='',stderr='')
            service=ApplicationService(base,base/'state',[],False,runner=runner)
            with patch('applications.service.require_session'):
                service.action('settings')
            self.assertEqual(commands[-1][-4:],['call','--','appearance','show'])

    def test_live_root_rejects_action_before_querying_or_writing(self):
        self.assertTrue((ROOT/'quickshell/applications/service.py').exists(), 'Guarded app service not implemented')
        Service=importlib.import_module('applications.service').ApplicationService
        with tempfile.TemporaryDirectory() as temp:
            service=Service(ROOT,Path(temp)/'state',ENTRIES,preview=True)
            with self.assertRaises(PermissionError):service.action('close',900)
            self.assertFalse((Path(temp)/'state').exists())

    def isolated(self, base):
        root=base/'config';root.mkdir(); state=base/'state/niri-shell';runtime=base/'runtime';runtime.mkdir()
        (base/'.appearance-preview.json').write_text(json.dumps(dict(root=str(root),state=str(state),runtime=str(runtime))))
        sock=socket.socket(socket.AF_UNIX);sock.bind(str(runtime/'niri.sock'));self.addCleanup(sock.close)
        return root,state,dict(NIRI_SHELL_PREVIEW='1',XDG_RUNTIME_DIR=str(runtime),NIRI_SOCKET=str(runtime/'niri.sock'))

    def test_stale_and_invalid_ids_never_reach_action_command(self):
        self.assertTrue((ROOT/'quickshell/applications/service.py').exists(), 'Guarded app service not implemented')
        Service=importlib.import_module('applications.service').ApplicationService
        with tempfile.TemporaryDirectory() as temp:
            root,state,env=self.isolated(Path(temp))
            def runner(argv,**kwargs):
                self.assertEqual(argv,['niri','msg','-j','windows'])
                from subprocess import CompletedProcess
                return CompletedProcess(argv,0,json.dumps(WINDOWS),'')
            with patch.dict(os.environ,env):
                service=Service(root,state,ENTRIES,preview=True,runner=runner)
                for identifier in (True,'12',-1,2**64,123456):
                    with self.assertRaises((ValueError,RuntimeError)):service.action('close',identifier)
                with self.assertRaises(ValueError):service.action('minimize',12)
                with self.assertRaises(ValueError):service.action('maximize',12)

    def test_preview_blocks_external_launches_and_unknown_desktop_ids(self):
        self.assertTrue((ROOT/'quickshell/applications/service.py').exists(), 'Guarded app service not implemented')
        Service=importlib.import_module('applications.service').ApplicationService
        with tempfile.TemporaryDirectory() as temp:
            root,state,env=self.isolated(Path(temp))
            with patch.dict(os.environ,env):
                service=Service(root,state,ENTRIES,preview=True)
                with self.assertRaises(ValueError):service.action('launch','firefox.desktop')
                with self.assertRaises(ValueError):service.action('launch','../../bin/bash')
            self.assertFalse(state.exists())

    def test_settings_child_output_does_not_corrupt_json_channel(self):
        import subprocess
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root,state,env=self.isolated(base)
            binary=base/'qs'
            binary.write_text('#!'+sys.executable+'\nimport sys\nif sys.argv[1]=="ipc": sys.exit(1)\nprint("Settings process started",flush=True)\n')
            binary.chmod(0o700)
            env=dict(os.environ,**env,PATH=str(base)+os.pathsep+os.environ['PATH'])
            code='from applications.service import ApplicationService; import json; from pathlib import Path; s=ApplicationService(Path('+repr(str(root))+'),Path('+repr(str(state))+'),[],True); s.action("settings"); [p.wait(timeout=3) for p in s.children]; print(json.dumps({"done":True})); s.close()'
            result=subprocess.run([sys.executable,'-c',code],env=dict(env,PYTHONPATH=str(ROOT/'quickshell')),capture_output=True,text=True,check=True)
            self.assertEqual(result.stdout.strip(),'{"done": true}')

if __name__=='__main__':unittest.main()
