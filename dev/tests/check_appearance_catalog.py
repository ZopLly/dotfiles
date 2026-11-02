#!/usr/bin/env python3
"""Catalogue behavior: original colors, complete local assets, and safe resolution."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'quickshell'))
from appearance.catalog import Catalogue
from appearance.palette import resolve_palette

class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = Catalogue(ROOT)

    def test_all_groups_are_distinct_and_wallpapers_are_preserved(self):
        themes = self.catalogue.themes()
        self.assertEqual(len(themes),22)
        self.assertEqual(len({t['id'] for t in themes}),22)
        self.assertEqual(sum(t['group']=='legacy' for t in themes),4)
        self.assertEqual(len(self.catalogue.wallpapers()),11)
        inventory=json.loads((ROOT/'docs/APPEARANCE-ASSET-INVENTORY.json').read_text())
        expected={w['sha256'] for w in inventory['wallpapers']}
        actual={hashlib.sha256(self.catalogue.wallpaper(w['id'])['path'].read_bytes()).hexdigest() for w in self.catalogue.wallpapers()}
        self.assertEqual(actual,expected)
        gif=next(w for w in self.catalogue.wallpapers() if w['frames']>1)
        self.assertEqual(gif['frames'],34)
        self.assertEqual(self.catalogue.wallpaper(gif['id'])['path'].suffix,'.gif')

    def test_original_rgb_and_accent_selection(self):
        p=resolve_palette(self.catalogue,'hyprstack:catppuccin','dark')
        self.assertEqual((p['bg'],p['fg'],p['accent']),('#1e1e2e','#cdd6f4','#cba6f7'))
        self.assertEqual(p['ansi'][1],'#f38ba8')
        blue=resolve_palette(self.catalogue,'hyprstack:catppuccin','light','blue')
        self.assertEqual((blue['bg'],blue['accent']),('#eff1f5','#1e66f5'))
        old=resolve_palette(self.catalogue,'legacy:ancient-odyssey')
        self.assertEqual(old['bg'].lower(),'#17283a')
        self.assertEqual(old['accent'].lower(),'#81b5d5')

    def test_modes_are_complete_and_invalid_choices_fail(self):
        for t in self.catalogue.themes():
            for mode in t['modes']:
                self.assertTrue(resolve_palette(self.catalogue,t['id'],mode)['fg'].startswith('#'))
        for args in [('bad',None,None),('hyprstack:catppuccin','sepia',None),('hyprstack:catppuccin','dark','invalid'),('legacy:tokyo-night','light',None)]:
            with self.assertRaises(ValueError):resolve_palette(self.catalogue,*args)
        with self.assertRaises(ValueError):self.catalogue.wallpaper('../../.ssh/id_rsa')

    def test_individual_legacy_asset_symlinks_cannot_escape(self):
        from appearance.render import render_theme
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'root'
            shutil.copytree(ROOT/'assets',root/'assets',symlinks=False)
            outside=Path(temp)/'outside';outside.write_text('outside')
            path=root/'assets/themes/ancient-odyssey/eww.scss'
            path.unlink();path.symlink_to(outside)
            c=Catalogue(root)
            selection=dict(palette_id='legacy:ancient-odyssey',mode=None,accent_id=None)
            with self.assertRaises(ValueError):render_theme(c,selection)
            path=root/'assets/themes/ancient-odyssey/waybar.css'
            path.unlink();path.symlink_to(outside)
            with self.assertRaises(ValueError):resolve_palette(c,'legacy:ancient-odyssey')
            from appearance.store import initial_selection
            with self.assertRaises(ValueError):initial_selection(c)

    def test_migration_does_not_read_current_color_file_outside_root(self):
        from appearance.store import initial_selection
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'root'
            shutil.copytree(ROOT/'assets',root/'assets',symlinks=False)
            outside=Path(temp)/'external.css'
            outside.write_bytes((root/'assets/themes/ancient-odyssey/waybar.css').read_bytes())
            candidate=root/'assets/themes/current/waybar.css'
            candidate.unlink();candidate.symlink_to(outside)
            selected=initial_selection(Catalogue(root))
            self.assertIsNone(selected['palette_id'])

    def test_catalogue_relocates_and_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            shutil.copytree(ROOT/'assets/appearance',root/'assets/appearance')
            shutil.copytree(ROOT/'assets/wallpapers/library',root/'assets/wallpapers/library')
            shutil.copytree(ROOT/'assets/themes',root/'assets/themes',symlinks=True)
            c=Catalogue(root)
            first=c.wallpapers()[0]
            path=c.wallpaper(first['id'])['path']
            self.assertTrue(path.is_relative_to(root))
            outside=root.parent/'outside-wallpaper-test'
            outside.write_text('outside')
            try:
                path.unlink();path.symlink_to(outside)
                with self.assertRaises(ValueError):c.wallpaper(first['id'])
            finally:outside.unlink()

if __name__=='__main__':unittest.main()
