#!/usr/bin/env python3
"""Independent appearance choices and actual rendered consumer files."""
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'quickshell'))
from appearance.catalog import Catalogue
from appearance.render import render_theme
from appearance.store import Store, initial_selection

class StateTests(unittest.TestCase):
    def setUp(self):
        self.catalogue=Catalogue(ROOT)

    def test_missing_state_does_not_write_and_changes_stay_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'new/appearance.json';s=Store(path,self.catalogue)
            original=s.load()
            self.assertFalse(path.parent.exists())
            changed=s.change(original,palette_id='hyprstack:catppuccin',mode='light',accent_id='blue')
            self.assertEqual(changed['wallpaper_id'],original['wallpaper_id'])
            image=self.catalogue.wallpapers()[-1]['id']
            wallpaper=s.change(changed,wallpaper_id=image)
            self.assertEqual((wallpaper['palette_id'],wallpaper['mode'],wallpaper['accent_id']),('hyprstack:catppuccin','light','blue'))
            s.save(changed);s.save(wallpaper)
            self.assertEqual(s.load(),wallpaper)
            self.assertEqual(json.loads(path.with_suffix('.json.bak').read_text()),changed)
            self.assertEqual(path.stat().st_mode&0o777,0o600)
            before=path.read_bytes()
            with self.assertRaises(ValueError):s.change(wallpaper,palette_id='../../bad')
            self.assertEqual(path.read_bytes(),before)

    def test_corrupt_state_and_symlink_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'appearance.json';path.write_text('{broken')
            s=Store(path,self.catalogue)
            with self.assertRaises(ValueError):s.load()
            with self.assertRaises(ValueError):s.save(initial_selection(self.catalogue))
            self.assertEqual(path.read_text(),'{broken')
            path.unlink();target=Path(temp)/'outside';target.write_text('keep')
            path.symlink_to(target)
            with self.assertRaises(ValueError):s.save(initial_selection(self.catalogue))
            self.assertEqual(target.read_text(),'keep')

    def test_all_variants_render_real_toml_and_standalone_lock_css(self):
        selection=initial_selection(self.catalogue)
        for t in self.catalogue.themes():
            for mode in t['modes']:
                value=dict(selection,palette_id=t['id'],mode=mode,accent_id=None)
                rendered=render_theme(self.catalogue,value)
                terminal=tomllib.loads(rendered['alacritty.toml'].decode())
                self.assertIn('background',terminal['colors']['primary'])
                self.assertIn('focus-ring',rendered['niri-runtime.kdl'].decode())
                self.assertNotIn('../../../',rendered['gtklock.css'].decode())
        c=dict(selection,palette_id='hyprstack:catppuccin',mode='light',accent_id='blue')
        files=render_theme(self.catalogue,c)
        terminal=tomllib.loads(files['alacritty.toml'].decode())
        self.assertEqual(terminal['colors']['primary']['background'],'#eff1f5')
        self.assertEqual(terminal['colors']['normal']['red'],'#d20f39')
        self.assertEqual(json.loads(files['palette.json'])['accent'],'#1e66f5')

    def test_validated_backup_can_recover_corrupt_state_without_losing_it(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'appearance.json';s=Store(path,self.catalogue)
            original=s.load();s.save(original)
            s.save(s.change(original,palette_id='hyprstack:catppuccin'))
            path.write_text('{corrupt')
            restored=s.restore_backup()
            self.assertEqual(restored,original)
            self.assertEqual(s.load(),original)
            archives=list(path.parent.glob('appearance.corrupt-*.json'))
            self.assertEqual(len(archives),1)
            self.assertEqual(archives[0].read_text(),'{corrupt')
            self.assertEqual(archives[0].stat().st_mode&0o777,0o600)

    def test_legacy_terminal_values_remain_exact(self):
        for t in self.catalogue.themes()[:4]:
            state=dict(initial_selection(self.catalogue),palette_id=t['id'],mode=None,accent_id=None)
            self.assertEqual(render_theme(self.catalogue,state)['alacritty.toml'],(self.catalogue.theme(t['id'])['path']/'alacritty.toml').read_bytes())

if __name__=='__main__':unittest.main()
