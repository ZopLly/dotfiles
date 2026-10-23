#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quickshell'))
from floating_resize import resize
class ResizeTests(unittest.TestCase):
 def rpc(self,request):
  if request=='Windows':return {'Windows':[dict(id=5,pid=10,is_floating=self.floating,is_focused=True,workspace_id=1,layout=dict(tile_pos_in_workspace_view=[100,80],window_offset_in_tile=[0,0],window_size=[self.width,200]))]}
  if request=='Workspaces':return {'Workspaces':[dict(id=1,output='test',is_active=True)]}
  action=request['Action'];self.actions.append(action)
  if 'SetWindowWidth' in action:self.width=min(400,action['SetWindowWidth']['change']['SetFixed'])
  return 'Handled'
 def setUp(self):self.actions=[];self.floating=True;self.width=300
 def request(self):return dict(id=5,pid=10,output='test',width=500,height=250,right=400,bottom=None,final=True)
 def test_rejects_tiled_and_reused_window_before_mutation(self):
  self.floating=False
  with self.assertRaises(ValueError):resize(self.request(),self.rpc)
  self.assertEqual(self.actions,[])
  self.floating=True;request=self.request();request['pid']=99
  with self.assertRaises(ValueError):resize(request,self.rpc)
  self.assertEqual(self.actions,[])
 def test_resize_and_anchor_respect_actual_client_size(self):
  with patch('floating_resize.time.sleep'):resize(self.request(),self.rpc)
  self.assertEqual(self.actions[0],{'SetWindowWidth':{'id':5,'change':{'SetFixed':500}}})
  self.assertEqual(self.actions[-1],{'MoveFloatingWindow':{'id':5,'x':{'AdjustFixed':-100.0},'y':{'AdjustFixed':0.0}}})
 def test_switch_to_tiling_stops_the_second_size_action(self):
  def command(request):
   result=self.rpc(request)
   if isinstance(request,dict) and 'SetWindowWidth' in request.get('Action',{}):self.floating=False
   return result
  with self.assertRaises(ValueError):resize(self.request(),command)
  self.assertEqual(len(self.actions),1)
  self.assertIn('SetWindowWidth',self.actions[0])
 def test_invalid_geometry_cannot_reach_niri_actions(self):
  for field,value in [('width',float('nan')),('height',-5),('right',float('inf'))]:
   request=self.request();request[field]=value
   with self.assertRaises(ValueError):resize(request,self.rpc)
  self.assertEqual(self.actions,[])
if __name__=='__main__':unittest.main()
