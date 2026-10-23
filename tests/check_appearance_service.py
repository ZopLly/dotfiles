#!/usr/bin/env python3
"""A real disposable filesystem with fake compositor commands at the external boundary."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'quickshell'))
from appearance.service import AppearanceService

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='niri-appearance-test-')
        self.base=Path(self.temp.name);self.root=self.base/'config'
        shutil.copytree(ROOT/'assets',self.root/'assets',symlinks=False)
        shutil.copytree(ROOT/'gtklock',self.root/'gtklock',symlinks=False)
        self.runtime=self.base/'runtime';self.runtime.mkdir()
        self.socket=socket.socket(socket.AF_UNIX);self.socket.bind(str(self.runtime/'niri.sock'))
        self.state=self.base/'state/niri-shell'
        (self.base/'.appearance-preview.json').write_text(json.dumps({'root':str(self.root),'state':str(self.state),'runtime':str(self.runtime)}))
        self.env=patch.dict(os.environ,{'NIRI_SHELL_PREVIEW':'1','XDG_RUNTIME_DIR':str(self.runtime),'NIRI_SOCKET':str(self.runtime/'niri.sock')})
        self.env.start();self.image='';self.wallpaper_fail=False
        self.service=AppearanceService(self.root,self.state,True,runner=self.run_external)

    def tearDown(self):
        self.env.stop();self.socket.close();self.temp.cleanup()

    def run_external(self,args,**kwargs):
        if args[:2]==['awww','img']:
            if self.wallpaper_fail:raise RuntimeError('test wallpaper failure')
            self.image=args[-1]
        return subprocess.CompletedProcess(args,0,stdout='test: currently displaying: image: '+self.image,stderr='')

    def test_palette_wallpaper_and_restart_are_independent(self):
        changed=self.service.select({'palette_id':'hyprstack:catppuccin','mode':'light','accent_id':'blue'})
        original_wallpaper=changed['selection']['wallpaper_id']
        target=self.service.catalogue.wallpapers()[-1]['id']
        changed=self.service.select({'wallpaper_id':target})
        self.assertEqual(changed['selection']['mode'],'light')
        self.assertEqual(changed['selection']['accent_id'],'blue')
        self.assertEqual(changed['selection']['wallpaper_id'],target)
        self.assertNotEqual(target,original_wallpaper)
        p=json.loads((self.root/'assets/themes/current/palette.json').read_text())
        self.assertEqual(p['accent'],'#1e66f5')
        again=AppearanceService(self.root,self.state,True,runner=self.run_external)
        self.assertEqual(again.snapshot()['selection'],changed['selection'])
        self.assertEqual((self.root/'assets/themes/ancient-odyssey/waybar.css').read_bytes(),(ROOT/'assets/themes/ancient-odyssey/waybar.css').read_bytes())

    def test_live_reload_failure_reloads_restored_palette(self):
        (self.root/'niri').mkdir();(self.root/'niri/config.kdl').write_text('')
        (self.root/'alacritty').mkdir();(self.root/'alacritty/niri.toml').write_text('')
        before=(self.service.current/'waybar.css').read_bytes();reloads=[]
        def runner(args,**kwargs):
            if args==['makoctl','reload']:
                reloads.append((self.service.current/'waybar.css').read_bytes())
                if len(reloads)==1:raise RuntimeError('Notification reload failed')
            return self.run_external(args,**kwargs)
        self.service.preview=False;self.service.runner=runner
        with patch('appearance.service.require_session'):
            with self.assertRaises(RuntimeError):self.service.select({'palette_id':'hyprstack:catppuccin','mode':'light'})
        self.assertGreaterEqual(len(reloads),2)
        self.assertEqual(reloads[-1],before)
        self.assertEqual((self.service.current/'waybar.css').read_bytes(),before)

    def test_wallpaper_failure_is_visible_without_false_selection(self):
        before=self.service.snapshot()['selection']
        self.wallpaper_fail=True
        result=self.service.select({'wallpaper_id':self.service.catalogue.wallpapers()[-1]['id']})
        self.assertEqual(result['selection']['wallpaper_id'],before['wallpaper_id'])
        self.assertIn('test wallpaper failure',result['error'])
        self.assertEqual(result['wallpaper_status'],'unconfirmed')

    def test_query_failure_tracks_uncertainty_and_old_choice_can_restore(self):
        before=self.service.snapshot()['selection']
        real=self.service.runner
        def fail_query(args,**kwargs):
            if args[:2]==['awww','query']:raise RuntimeError('query failed')
            return real(args,**kwargs)
        self.service.runner=fail_query
        target=self.service.catalogue.wallpapers()[-1]['id']
        result=self.service.select({'wallpaper_id':target})
        self.assertEqual(result['wallpaper_status'],'unconfirmed')
        self.assertEqual(result['requested_wallpaper_id'],target)
        self.assertEqual(result['selection']['wallpaper_id'],before['wallpaper_id'])
        restarted=AppearanceService(self.root,self.state,True,runner=real)
        self.assertEqual(restarted.snapshot()['wallpaper_status'],'unconfirmed')
        restored=restarted.select({'wallpaper_id':before['wallpaper_id']})
        self.assertEqual(restored['wallpaper_status'],'confirmed')
        self.assertEqual(self.image,str(self.service.catalogue.wallpaper(before['wallpaper_id'])['path']))

    def test_staging_and_wrong_socket_are_rejected_before_writes(self):
        with self.assertRaises(PermissionError):
            AppearanceService(ROOT,self.state,True,runner=self.run_external).select({'palette_id':'hyprstack:catppuccin'})
        with patch.dict(os.environ,{'NIRI_SOCKET':'/tmp/host-niri.sock'}):
            with self.assertRaises(PermissionError):self.service.select({'palette_id':'hyprstack:catppuccin'})
        with self.assertRaises(PermissionError):
            AppearanceService(self.root,self.state,False,runner=self.run_external).select({'palette_id':'hyprstack:catppuccin'})
        self.assertFalse(self.state.exists())

    def test_failed_journal_write_keeps_current_directory(self):
        before=(self.root/'assets/themes/current/waybar.css').read_bytes()
        with patch.object(self.service.store,'_write',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.service.select({'palette_id':'hyprstack:catppuccin'})
        self.assertEqual((self.root/'assets/themes/current/waybar.css').read_bytes(),before)

    def test_failed_state_commit_restores_original_appearance(self):
        before=(self.root/'assets/themes/current/waybar.css').read_bytes()
        with patch.object(self.service.store,'save',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.service.select({'palette_id':'hyprstack:catppuccin'})
        self.assertEqual((self.root/'assets/themes/current/waybar.css').read_bytes(),before)
        self.assertFalse((self.state/'appearance.json').exists())
        self.assertFalse((self.state/'transition.json').exists())

if __name__=='__main__':unittest.main()
