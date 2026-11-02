#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'quickshell'))
from applications.usage import Usage
class UsageTests(unittest.TestCase):
 def test_focus_changes_are_counted_and_persisted_without_window_titles(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'usage.json';usage=Usage(path)
   usage.observe('firefox.desktop');usage.observe('firefox.desktop')
   usage.observe('chatgpt.desktop');usage.observe('firefox.desktop')
   self.assertEqual(usage.counts,{'firefox.desktop':2,'chatgpt.desktop':1})
   self.assertEqual(Usage(path).counts,usage.counts)
   self.assertEqual(path.stat().st_mode & 0o777,0o600)
   self.assertNotIn('title',path.read_text())
 def test_invalid_or_unknown_identifiers_do_not_get_recorded(self):
  with tempfile.TemporaryDirectory() as temp:
   usage=Usage(Path(temp)/'usage.json')
   for value in (None,'window-app:unknown','../private.desktop','a'*300+'.desktop'):
    usage.observe(value)
   self.assertEqual(usage.counts,{})
 def test_broken_file_does_not_destroy_other_files(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'usage.json';path.write_text('{broken')
   usage=Usage(path);self.assertEqual(usage.counts,{})
   self.assertEqual(path.read_text(),'{broken')
if __name__=='__main__':unittest.main()
