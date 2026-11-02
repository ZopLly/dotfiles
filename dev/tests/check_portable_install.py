#!/usr/bin/env python3
"""Full install/rollback under a disposable HOME; never modifies the current session."""
import json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='niri-install-test-') as folder:
 home=Path(folder);config=home/'.config';state=home/'.local/state'
 original=config/'niri';original.mkdir(parents=True);(original/'personal.txt').write_text('preserved')
 binary=home/'bin';binary.mkdir();ctl=binary/'systemctl';ctl.write_text('#!/bin/sh\nexit 0\n');ctl.chmod(0o755)
 env=dict(os.environ,HOME=str(home),XDG_CONFIG_HOME=str(config),XDG_STATE_HOME=str(state),XDG_CACHE_HOME=str(home/'.cache'),PATH=str(binary)+':'+os.environ['PATH'])
 result=subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--portable','--apply'],env=env,text=True,capture_output=True)
 assert result.returncode==0,result.stdout+result.stderr
 release=(config/'niri').resolve().parent
 marker=json.loads((release/'.shell-release.json').read_text())
 assert marker==dict(schema=1,root=str(release),state=str(state/'niri-shell'))
 assert (release/'niri/personal.txt').read_text()=='preserved'
 assert (release/'niri/conf.d/outputs.kdl').read_text()=='// Outputs are detected automatically.\n'
 assert 'launcher' in (release/'niri/conf.d/binds.kdl').read_text()
 assert (release/'alacritty/niri.toml').is_file()
 assert (release/'quickshell/StateMerge.js').is_file()
 assert (release/'quickshell/cava_stream.py').is_file()
 for name in ('tests','dev','legacy','waybar','eww','archive'):
  assert not (release/name).exists(),name
 assert (release/'gtklock/modules/layout-module.so').stat().st_size>0
 assert '/home/andrew' not in (release/'systemd/user/swayidle.service').read_text()
 assert str(home/'.config/gtklock/scripts/lock.sh') in (release/'systemd/user/swayidle.service').read_text()
 manifest=next((state/'dotfiles/backups').glob('*/manifest.json'))
 subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--rollback',str(manifest),'--apply'],env=env,check=True,stdout=subprocess.DEVNULL)
 assert not original.is_symlink() and (original/'personal.txt').read_text()=='preserved'
 assert not (config/'quickshell').exists()
print('PASS: portable install, native guard marker, built modules, automatic outputs, preserved personal extras and rollback')
