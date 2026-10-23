#!/usr/bin/env python3
"""Deploy tested Minimal gtklock files without locking or restarting the session."""
import argparse,datetime,importlib.util,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deploy',ROOT/'scripts/apply-odyssey.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def payload():
    names=['gtklock/config.ini','gtklock/layout.xml','gtklock/style.css','gtklock/minimal.css','gtklock/scripts/lock.sh','gtklock/scripts/blur-background.sh','gtklock/modules/minimal-module.so']
    names += ['assets/themes/'+theme+'/gtklock.css' for theme in ('ancient-odyssey','catppuccin-mocha','gruvbox-dark','tokyo-night')]
    return {name:(ROOT/name).read_bytes() for name in names}
def restore(folder):
    manifest=json.loads((folder/'manifest.json').read_text());live=Path(manifest['live'])
    for item in manifest['files']:
        target=live/item['name'];saved=folder/'files'/item['name'];allowed={item['installed']}
        if saved.exists():allowed.add(h.digest(saved.read_bytes()))
        if target.exists() and h.digest(target.read_bytes()) not in allowed:raise RuntimeError('Edited after deployment: '+str(target))
    for item in manifest['files']:
        target=live/item['name']
        if item['existed']:h.atomic(target,(folder/'files'/item['name']).read_bytes(),item['mode'])
        elif target.exists():target.unlink()
    for index,path in enumerate(manifest.get('cache',[])):
        cache=Path(path)
        saved=folder/('old-blur'+('.jpg' if index==0 else '.jpg.signature'))
        if saved.exists():h.atomic(cache,saved.read_bytes(),0o600)
        elif cache.exists():cache.unlink()
    print('Restored:',folder)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--rollback',type=Path);args=p.parse_args()
    if args.rollback:
        if args.apply:restore(args.rollback)
        else:print('Rollback:',args.rollback)
        return
    live=(Path.home()/'.config/gtklock').resolve().parent
    if (live/'.git').exists() or not(live/'gtklock/scripts/lock.sh').is_file():raise RuntimeError('Expected installed snapshot')
    if not subprocess.check_output(['gtklock','--version'],text=True).strip().startswith('gtklock v4.0.'):raise RuntimeError('Module audited for gtklock 4.0 only')
    subprocess.run(['python3',str(ROOT/'scripts/lockscreen-tokens.py'),'--check'],check=True)
    files=payload();print('Target:',live);print('Files:',*files,sep='\n');print('No lock, service change, session restart or PAM changes.')
    if not args.apply:return
    if subprocess.run(['pgrep','-u',str(os.getuid()),'-x','gtklock'],stdout=subprocess.DEVNULL).returncode==0:raise RuntimeError('Unlock existing gtklock before deployment')
    folder=Path.home()/'.local/state/dotfiles/lockscreen-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');folder.mkdir(parents=True,mode=0o700)
    manifest={'live':str(live),'files':[],'cache':[]}
    for name,data in files.items():
        target=live/name
        if target.is_symlink():raise RuntimeError('Unexpected symlink: '+name)
        exists=target.exists();mode=target.stat().st_mode&0o777 if exists else 0o755 if name.endswith('.sh') else 0o644
        if exists:
            saved=folder/'files'/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
        manifest['files'].append(dict(name=name,existed=exists,mode=mode,installed=h.digest(data)))
    cache=Path(os.environ.get('XDG_CACHE_HOME',str(Path.home()/'.cache')))
    theme=(live/'assets/themes/current').resolve().name
    # Keep the previous blur and signature as part of the same rollback manifest.
    for suffix in ('.jpg','.jpg.signature'):
        target=cache/('gtklock-'+theme+suffix)
        if target.exists():shutil.copy2(target,folder/('old-blur'+suffix))
        manifest['cache'].append(str(target))
    h.atomic(folder/'manifest.json',json.dumps(manifest,indent=2).encode(),0o600)
    try:
        for item in manifest['files']:h.atomic(live/item['name'],files[item['name']],item['mode'])
        subprocess.run(['bash',str(live/'gtklock/scripts/blur-background.sh')],check=True,timeout=30)
    except BaseException:
        restore(folder);raise
    print('Applied for NEXT lock. Backup:',folder)
if __name__=='__main__':main()
