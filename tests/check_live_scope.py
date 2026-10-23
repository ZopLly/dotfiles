import json,os,socket,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quickshell'))
class LiveScopeTests(unittest.TestCase):
 def test_only_active_marked_release_can_mutate_session(self):
  import preview_scope
  self.assertTrue(hasattr(preview_scope,'require_session'),'Live release authorization not implemented')
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);root=home/'.local/state/dotfiles/releases/candidate';root.mkdir(parents=True);state=home/'.local/state/niri-shell';runtime=home/'runtime';runtime.mkdir()
   config=home/'.config';config.mkdir()
   for name in ['niri','quickshell']:
    (root/name).mkdir();(config/name).symlink_to(root/name)
   sock=socket.socket(socket.AF_UNIX);self.addCleanup(sock.close);sock.bind(str(runtime/'niri.sock'))
   env=dict(NIRI_SHELL_PREVIEW='0',XDG_RUNTIME_DIR=str(runtime),NIRI_SOCKET=str(runtime/'niri.sock'))
   with patch.object(Path,'home',return_value=home),patch.dict(os.environ,env):
    with self.assertRaises(PermissionError):preview_scope.require_session(root,state,False)
    (root/'.shell-release.json').write_text(json.dumps(dict(schema=1,root=str(root),state=str(state))))
    preview_scope.require_session(root,state,False)
    (config/'niri').unlink();(config/'niri').symlink_to(home/'different')
    with self.assertRaises(PermissionError):preview_scope.require_session(root,state,False)
if __name__=='__main__':unittest.main()
