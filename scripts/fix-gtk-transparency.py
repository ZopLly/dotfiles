#!/usr/bin/env python3
"""Plan or safely remove the broken global Hyprstack CSS import in GTK 3/4."""
import argparse,datetime,hashlib,json,os,re,sys,tempfile
from pathlib import Path
START='/* >>> Hyprstack theme >>> */'
END='/* <<< Hyprstack theme <<< */'
PATTERN=re.compile(re.escape(START)+r'\s*\n\s*@import\s+url\("hyprstack-colors\.css"\);\s*\n\s*'+re.escape(END)+r'\s*\n?')

def remove_broken_import(text):
    matches=list(PATTERN.finditer(text))
    if text.count(START)!=len(matches) or text.count(END)!=len(matches) or len(matches)>1:
        raise ValueError('Hyprstack block was modified; refusing to overwrite it')
    return PATTERN.sub('',text)

def atomic_write(path,data,mode):
    fd,tmp=tempfile.mkstemp(prefix='.gtk-fix-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data)
        os.chmod(tmp,mode);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--rollback',type=Path,metavar='MANIFEST')
    parser.add_argument('--config-root',type=Path,default=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config')))
    parser.add_argument('--backup-root',type=Path,default=Path(os.environ.get('XDG_STATE_HOME',Path.home()/'.local/state'))/'niri-shell/gtk-repairs')
    args=parser.parse_args();changes=[]
    if args.rollback:
        if not args.apply:
            print('Preview rollback:',args.rollback,'(add --apply)');return
        manifest=args.rollback.resolve();records=json.loads(manifest.read_text())
        allowed={(args.config_root/f'gtk-{v}'/'gtk.css').absolute() for v in ('3.0','4.0')}
        for item in records:
            path=Path(item['path']);backup=Path(item['backup']).resolve()
            if path not in allowed or path.is_symlink() or backup.parent!=manifest.parent or not backup.is_file():raise ValueError('Invalid rollback manifest')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=item['installed_sha256']:raise ValueError(f'GTK config changed after repair: {path}')
        for item in records:atomic_write(Path(item['path']),Path(item['backup']).read_bytes(),item['mode'])
        manifest.rename(manifest.with_name('manifest.restored.json'))
        print('GTK configuration restored');return
    for version in ('3.0','4.0'):
        path=args.config_root/f'gtk-{version}'/'gtk.css'
        if path.is_symlink():raise ValueError(f'Refusing to overwrite symlink: {path}')
        if not path.exists():continue
        raw=path.read_bytes();changed=remove_broken_import(raw.decode()).encode()
        if changed!=raw:changes.append((path,raw,changed,path.stat().st_mode&0o777))
    print('Broken GTK imports found:',len(changes))
    if not args.apply:
        print('Preview only; no files changed.')
        return
    if not changes:return
    backup=args.backup_root/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True,mode=0o700)
    records=[]
    for index,(path,old,new,mode) in enumerate(changes):
        target=backup/f'{index}.css';target.write_bytes(old);target.chmod(0o600)
        records.append(dict(path=str(path.absolute()),backup=str(target.resolve()),mode=mode,installed_sha256=hashlib.sha256(new).hexdigest()))
    (backup/'manifest.json').write_text(json.dumps(records,indent=2));(backup/'manifest.json').chmod(0o600)
    changed=[]
    try:
        for path,old,new,mode in changes:
            if path.is_symlink() or path.read_bytes()!=old:raise ValueError(f'GTK config changed during repair: {path}')
            atomic_write(path,new,mode);changed.append((path,old,mode))
    except BaseException:
        for path,old,mode in reversed(changed):atomic_write(path,old,mode)
        raise
    print('GTK repair saved; backup:',backup)
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,UnicodeError) as error:sys.exit(str(error))
