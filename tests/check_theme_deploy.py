#!/usr/bin/env python3
"""Check the visual-only payload without running installers or theme switchers."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deploy',ROOT/'scripts/apply-odyssey.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)
files=deploy.payload(Path('/tmp/installed-snapshot'))
assert 'quickshell/backend.py' not in files
assert 'niri/config.kdl' not in files
assert not any('widgets.json' in name for name in files)
assert b'rgba(' not in files['assets/themes/ancient-odyssey/waybar.css']
assert b'shell_bg_modules #f217283a' in files['assets/themes/ancient-odyssey/waybar.css']
old=subprocess.check_output(['git','-C',str(ROOT),'show','50983aa:quickshell/shell.qml'],text=True)
new=files['quickshell/shell.qml'].decode()
assert len(old.splitlines())==len(new.splitlines())
assert sum(a!=b for a,b in zip(old.splitlines(),new.splitlines()))==1
print('PASS: theme-only payload excludes backend, Niri and widget settings; one palette mapping change')
if '--gui-copy' in sys.argv:
 base=Path(tempfile.mkdtemp(prefix='odyssey-theme-only-'))
 for name in ('scripts','niri','assets','quickshell','eww','waybar','alacritty','fuzzel','tests'):
  shutil.copytree(ROOT/name,base/name,symlinks=False,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 shutil.copy2(ROOT/'preview.sh',base/'preview.sh')
 for name in subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only','50983aa','quickshell'],text=True).splitlines():
  (base/name).write_bytes(subprocess.check_output(['git','-C',str(ROOT),'show','50983aa:'+name]))
 for name,data in files.items():
  if name.startswith(('quickshell/','assets/')):
   (base/name).parent.mkdir(parents=True,exist_ok=True);(base/name).write_bytes(data)
 # OSD belongs to the separate hardware update and is excluded from this smoke.
 p=base/'scripts/preview.py';s=p.read_text();a=s.index("                subprocess.run(['qs', 'ipc', 'call', 'shell', 'previewOsd', 'brightness']");b=s.index("                (base/'widget-checks.json')",a);s=s[:a]+s[b:];p.write_text(s.replace(str(ROOT),str(base)))
 # Keep preview paths inside the disposable copy.
 for name in ('niri/config.kdl','alacritty/alacritty.toml','fuzzel/fuzzel.ini'):
  p=base/name;p.write_text(p.read_text().replace(str(ROOT),str(base)))
 print(base)
