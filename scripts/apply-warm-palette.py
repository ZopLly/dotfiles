#!/usr/bin/env python3
"""Apply only reviewed warm theme assets and Alacritty; default is a plan."""
import argparse, datetime, importlib.util, json, os, shutil, subprocess, tomllib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deploy',ROOT/'scripts/apply-odyssey.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

def payload():
    files={str(p.relative_to(ROOT)):p.read_bytes() for p in (ROOT/'assets/themes/ancient-odyssey').iterdir() if p.is_file()}
    files['assets/themes/ancient-odyssey/waybar.css']=(ROOT/'deployment/ancient-odyssey/waybar.css').read_bytes()
    for theme in ('catppuccin-mocha','gruvbox-dark','tokyo-night'):
        name=f'assets/themes/{theme}/terminal-opacity.toml';files[name]=(ROOT/name).read_bytes()
    # Relative import keeps the existing current-theme link authoritative.
    files['alacritty/alacritty.toml']=(ROOT/'alacritty/alacritty.toml').read_bytes().replace(b'"opacity.toml"',b'"../assets/themes/current/terminal-opacity.toml"')
    for name,data in files.items():
        if name.endswith('.toml'):tomllib.loads(data.decode())
    return files

def refresh(live):
    subprocess.run(['niri','validate','-c',str(live/'niri/config.kdl')],check=True)
    (live/'niri/config.kdl').touch()
    (live/'alacritty/alacritty.toml').touch()
    if shutil.which('makoctl'):subprocess.run(['makoctl','reload'],check=True)

def restore(folder):
    manifest=json.loads((folder/'manifest.json').read_text());live=Path(manifest['live'])
    for item in manifest['files']:
        target=live/item['name'];saved=folder/'files'/item['name']
        allowed={item['installed']}
        if saved.exists():allowed.add(h.digest(saved.read_bytes()))
        if target.exists() and h.digest(target.read_bytes()) not in allowed:raise RuntimeError('Edited after deployment: '+str(target))
    for item in manifest['files']:
        target=live/item['name']
        if item['existed']:h.atomic(target,(folder/'files'/item['name']).read_bytes(),item['mode'])
        elif target.exists():target.unlink()
    refresh(live)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');parser.add_argument('--rollback',type=Path);args=parser.parse_args()
    if args.rollback:
        if args.apply:restore(args.rollback)
        else:print('Rollback:',args.rollback)
        return
    live=(Path.home()/'.config/quickshell').resolve().parent
    if (live/'.git').exists() or not (live/'quickshell/shell.qml').exists():raise RuntimeError('Expected installed snapshot')
    if (live/'assets/themes/current').resolve()!=live/'assets/themes/ancient-odyssey':raise RuntimeError('Ancient Odyssey is not active')
    if (Path.home()/'.config/alacritty/alacritty.toml').resolve()!=live/'alacritty/alacritty.toml':raise RuntimeError('Unexpected terminal configuration')
    files={name:data for name,data in payload().items() if not (live/name).exists() or (live/name).read_bytes()!=data}
    print('Target:',live);print('Files:',*files,sep='\n')
    subprocess.run(['niri','validate','-c',str(ROOT/'niri/config.kdl')],check=True)
    if not args.apply:return
    # Freeze the audited current contents before writing; preserve any future edits on rollback.
    folder=Path.home()/'.local/state/dotfiles/palette-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');folder.mkdir(parents=True,mode=0o700)
    manifest={'live':str(live),'files':[]}
    for name,data in files.items():
        target=live/name;exists=target.exists();mode=target.stat().st_mode&0o777 if exists else 0o644
        if target.is_symlink():raise RuntimeError('Refusing to replace symlink: '+name)
        if exists:
            saved=folder/'files'/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
        manifest['files'].append({'name':name,'existed':exists,'mode':mode,'installed':h.digest(data)})
    h.atomic(folder/'manifest.json',json.dumps(manifest,indent=2).encode(),0o600)
    try:
        for item in manifest['files']:h.atomic(live/item['name'],files[item['name']],item['mode'])
        refresh(live)
    except BaseException:
        restore(folder);raise
    print('Applied. Backup:',folder)
if __name__=='__main__':main()
