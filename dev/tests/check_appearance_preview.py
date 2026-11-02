#!/usr/bin/env python3
"""Preparation must create only disposable copies and an isolated terminal profile."""
import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import tomllib
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('appearance_preview',ROOT/'scripts/appearance-preview.py')
preview=importlib.util.module_from_spec(spec);spec.loader.exec_module(preview)

class PreviewTests(unittest.TestCase):
    def test_screenshot_wait_rejects_incomplete_png(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'screenshot.png';path.write_bytes(b'partial')
            with self.assertRaises(RuntimeError):preview.wait_for_png(path,timeout=.05)
            Image.new('RGB',(10,10),'blue').save(path)
            self.assertEqual(preview.wait_for_png(path),path)

    def test_prepare_keeps_assets_local_and_terminal_independent(self):
        original=(ROOT/'alacritty/alacritty.toml').read_bytes()
        with tempfile.TemporaryDirectory(prefix='niri-appearance-prepare-') as temp:
            base=Path(temp);config=preview.prepare(base)
            self.assertTrue((base/'.appearance-preview.json').is_file())
            subprocess.run(['niri','validate','-c',str(config/'niri/config.kdl')],check=True,capture_output=True)
            terminal=tomllib.loads((config/'alacritty/niri.toml').read_text())
            self.assertNotIn('colors',terminal)
            self.assertEqual(terminal['font']['normal']['family'],'JetBrainsMono Nerd Font')
            self.assertIn(str(config/'assets/themes/current/alacritty.toml'),terminal['general']['import'])
            self.assertTrue((config/'quickshell/appearance-ui/shell.qml').is_file())
            self.assertFalse(any(p.is_symlink() for p in config.rglob('*')))
            self.assertEqual(len(list((config/'assets/wallpapers/library').iterdir())),11)
            self.assertFalse((base/'state/niri-shell/appearance.json').exists())
        self.assertEqual((ROOT/'alacritty/alacritty.toml').read_bytes(),original)

if __name__=='__main__':unittest.main()
