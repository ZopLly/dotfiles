#!/usr/bin/env python3
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'scripts/fix-gtk-transparency.py'
assert p.exists(),'GTK repair helper is missing'
spec=importlib.util.spec_from_file_location('gtk_fix',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class GtkFixTests(unittest.TestCase):
 def test_only_hyprstack_import_is_removed(self):
  text='before\n/* >>> Hyprstack theme >>> */\n@import url("hyprstack-colors.css");\n/* <<< Hyprstack theme <<< */\nafter\n'
  self.assertEqual(m.remove_broken_import(text),'before\nafter\n')
  self.assertEqual(m.remove_broken_import('unchanged\n'),'unchanged\n')
 def test_apply_and_rollback_only_the_two_gtk_files(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);config=root/'config';backup=root/'backups'
   original='prefix\n/* >>> Hyprstack theme >>> */\n@import url("hyprstack-colors.css");\n/* <<< Hyprstack theme <<< */\nsuffix\n'
   for version in ('3.0','4.0'):
    folder=config/('gtk-'+version);folder.mkdir(parents=True);(folder/'gtk.css').write_text(original)
   cmd=[sys.executable,str(p),'--config-root',str(config),'--backup-root',str(backup)]
   subprocess.run(cmd+['--apply'],check=True,capture_output=True)
   for version in ('3.0','4.0'):self.assertEqual((config/('gtk-'+version)/'gtk.css').read_text(),'prefix\nsuffix\n')
   manifest=next(backup.glob('*/manifest.json'))
   subprocess.run(cmd+['--rollback',str(manifest),'--apply'],check=True,capture_output=True)
   for version in ('3.0','4.0'):self.assertEqual((config/('gtk-'+version)/'gtk.css').read_text(),original)
 def test_refuses_unbalanced_or_modified_markers(self):
  for text in ('/* >>> Hyprstack theme >>> */\nmissing end', '/* >>> Hyprstack theme >>> */\ncustom user settings\n/* <<< Hyprstack theme <<< */'):
   with self.assertRaises(ValueError):m.remove_broken_import(text)
if __name__=='__main__':unittest.main()
