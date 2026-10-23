import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deploy',ROOT/'scripts/deploy-integrated.py');deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)
class RollbackTests(unittest.TestCase):
 def scenario(self,fail=False):
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);(home/'.config').mkdir();active=home/'active';old=home/'old';candidate=home/'first-release';candidate.mkdir()
   (home/'.config/quickshell').symlink_to(active/'quickshell')
   (candidate/'.deployment.json').write_text(json.dumps(dict(old=str(old),links={'quickshell':str(old/'quickshell')})))
   stopped=[]
   def stop(root):
    stopped.append(root)
    if fail:raise RuntimeError('Panel failed to stop')
   with patch.object(Path,'home',return_value=home),patch.object(deploy.shell,'stop',side_effect=stop),patch.object(deploy.shell,'start'),patch.object(deploy.subprocess,'run'):
    if fail:
     with self.assertRaises(RuntimeError):deploy.rollback(candidate)
     self.assertEqual((home/'.config/quickshell').readlink(),active/'quickshell')
    else:
     deploy.rollback(candidate);self.assertEqual(stopped,[active])
 def test_rollback_stops_current_release_even_when_restoring_an_older_manifest(self):self.scenario()
 def test_failed_stop_does_not_switch_links(self):self.scenario(True)
class IdleRollbackTests(unittest.TestCase):
 def test_idle_unit_is_restored_and_reloaded_with_the_shell(self):
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);config=home/'.config';unit=config/'systemd/user/swayidle.service'
   unit.parent.mkdir(parents=True);unit.symlink_to('/previous/installed-unit')
   (config/'quickshell').symlink_to(home/'active/quickshell')
   candidate=home/'candidate';candidate.mkdir()
   (candidate/'.deployment.json').write_text(json.dumps(dict(old=str(home/'old'),idle_active=True,
    links={'quickshell':str(home/'old/quickshell'),'systemd/user/swayidle.service':'/original/idle-unit'})))
   with patch.object(Path,'home',return_value=home),patch.object(deploy.shell,'stop'),patch.object(deploy.shell,'start'),patch.object(deploy.subprocess,'run') as run:
    deploy.rollback(candidate)
    self.assertEqual(unit.readlink(),Path('/original/idle-unit'))
    calls=[call.args[0] for call in run.call_args_list]
    self.assertIn(['systemctl','--user','daemon-reload'],calls)
    self.assertIn(['systemctl','--user','restart','swayidle.service'],calls)
if __name__=='__main__':unittest.main()
