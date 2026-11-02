#!/usr/bin/env python3
import importlib
from pathlib import Path
import sys,unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'quickshell'))
class LayoutTests(unittest.TestCase):
 def module(self):
  self.assertTrue((ROOT/'quickshell/applications/window_modes.py').exists(),'Layout snapshots not implemented')
  return importlib.import_module('applications.window_modes')
 def test_snapshot_keeps_columns_tiles_sizes_but_excludes_dialogs_and_other_desktops(self):
  windows=[dict(id=3,pid=30,workspace_id=42,is_floating=False,layout=dict(pos_in_scrolling_layout=[2,1],window_size=[400,800])),dict(id=1,pid=10,workspace_id=42,is_floating=False,layout=dict(pos_in_scrolling_layout=[1,1],window_size=[500,300])),dict(id=2,pid=20,workspace_id=42,is_floating=False,layout=dict(pos_in_scrolling_layout=[1,2],window_size=[500,500])),dict(id=4,workspace_id=42,is_floating=True,layout={}),dict(id=5,workspace_id=99,is_floating=False,layout={})]
  result=self.module().capture(windows,42)
  self.assertEqual([w['id'] for w in result],[1,2,3]);self.assertEqual(result[1]['position'],[1,2]);self.assertEqual(result[1]['size'],[500,500]);self.assertNotIn('title',result[0])
 def test_closed_moved_and_reused_window_ids_are_not_restored(self):
  saved=[dict(id=1,pid=10,position=[1,1],size=[500,300]),dict(id=2,pid=20,position=[1,2],size=[500,500]),dict(id=3,pid=30,position=[2,1],size=[400,800]),dict(id=4,pid=40,position=[3,1],size=[400,800])]
  live=[dict(id=2,pid=20,workspace_id=42),dict(id=3,pid=30,workspace_id=99),dict(id=4,pid=400,workspace_id=42)]
  result=self.module().survivors(saved,live,42)
  self.assertEqual([[w['id'] for w in col] for col in result],[[2]])
 def test_menu_focus_uses_last_focused_window_on_target_workspace(self):
  windows=[dict(id=1,workspace_id=42,is_focused=False,focus_timestamp={'secs':10,'nanos':0}),dict(id=2,workspace_id=42,is_focused=False,focus_timestamp={'secs':20,'nanos':0}),dict(id=3,workspace_id=99,is_focused=True,focus_timestamp={'secs':30,'nanos':0})]
  self.assertEqual(self.module().last_focus(windows,42),2)
 def test_controller_rejects_live_environment_before_writes(self):
  import tempfile
  with tempfile.TemporaryDirectory() as temp:
   controller=self.module().WindowModes(ROOT,Path(temp)/'state',False,lambda args: self.fail('Native command outside preview'))
   with self.assertRaises(PermissionError):controller.toggle('eDP-1')
   self.assertFalse((Path(temp)/'state').exists())
 def test_corrupt_saved_layout_is_rejected_before_any_native_command(self):
  import tempfile,json,os
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp);(state/'window-modes.json').write_text(json.dumps(dict(schema=1,session='private.sock',workspaces={'42':{'phase':'floating','windows':[{'id':'not-a-window'}]}})))
   controller=self.module().WindowModes(ROOT,state,False,lambda args:self.fail('Malformed snapshot reached native command'))
   with patch.dict(os.environ,NIRI_SOCKET='private.sock'):
    with self.assertRaises(ValueError):controller.status()
if __name__=='__main__' :unittest.main()
