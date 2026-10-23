#!/usr/bin/env python3
"""Validate deployment planning and overwrite guards without changing a session."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('shell_deploy',ROOT/'scripts/apply-shell-update.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class DeploymentTests(unittest.TestCase):
    def make_live(self,live):
        for name in subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only','50983aa','quickshell'],text=True).splitlines():
            p=live/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(d.helpers.original(name,live))
        for name,data in d.helpers.payload(live).items():
            if name.startswith('quickshell/'):
                (live/name).write_bytes(data)

    def test_plan_preserves_theme_and_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            live=Path(temp);self.make_live(live)
            before={p.name:p.read_bytes() for p in (live/'quickshell').iterdir() if p.is_file()}
            files=d.payload(live)
            self.assertIn('quickshell/backend.py',files)
            self.assertIn('quickshell/Osd.qml',files)
            self.assertTrue(all(n.startswith('quickshell/') for n in files))
            self.assertIn(b'shell_bg_modules',files['quickshell/shell.qml'])
            self.assertEqual(before,{p.name:p.read_bytes() for p in (live/'quickshell').iterdir() if p.is_file()})
            p=live/'quickshell/AudioModule.qml';p.write_bytes(p.read_bytes()+b'\n// user edit\n')
            with self.assertRaisesRegex(RuntimeError,'changed since audit'):d.payload(live)

    def test_accepts_audited_hardware_version_and_rejects_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            live=Path(temp)
            for name in subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only','8180586','quickshell'],text=True).splitlines():
                p=live/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(d.baseline(name,live))
            files=d.payload(live)
            self.assertIn('quickshell/state_cache.py',files)
            self.assertIn('quickshell/StateMerge.js',files)
            self.assertIn('quickshell/backend.py',files)
            p=live/'quickshell/backend.py';p.write_bytes(p.read_bytes()+b'\n# local user edit\n')
            with self.assertRaisesRegex(RuntimeError,'changed since audit'):d.payload(live)

    def test_refuse_starting_duplicate(self):
        with patch.object(d,'process_count',return_value=1),patch.object(d,'run') as run:
            with self.assertRaisesRegex(RuntimeError,'already running'):d.start(Path('/tmp/live'))
            run.assert_not_called()

unittest.main()
