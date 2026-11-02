#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
class PreviewTests(unittest.TestCase):
    def test_preparation_routes_menu_to_private_shell_and_keeps_catalogue(self):
        path=ROOT/'scripts/applications-preview.py'
        self.assertTrue(path.is_file(),'Integrated applications preview not implemented')
        spec=importlib.util.spec_from_file_location('applications_preview',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='niri-applications-test-') as temp:
            base=Path(temp);config=module.prepare(base)
            subprocess.run(['niri','validate','-c',str(config/'niri/config.kdl')],check=True,capture_output=True)
            entries=json.loads((base/'applications-catalogue.json').read_text())
            self.assertIn('firefox.desktop',[e['id'] for e in entries])
            self.assertTrue(all('exec' not in e for e in entries))
            self.assertFalse(any(p.is_symlink() for p in config.rglob('*')))
            self.assertFalse((base/'state/niri-shell/appearance.json').exists())
if __name__=='__main__':unittest.main()
