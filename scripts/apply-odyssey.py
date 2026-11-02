#!/usr/bin/env python3
"""Deploy only Ancient Odyssey visuals to the current snapshot, with file rollback."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = '50983aa'
VISUAL = ('quickshell/ActionButton.qml', 'quickshell/ThemedChoice.qml',
          'quickshell/CalendarCard.qml', 'scripts/theme-switcher.sh',
          'gtklock/scripts/lock.sh', 'gtklock/scripts/blur-background.sh', 'mako/config')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def original(name, live):
    data = subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE+':'+name])
    try:
        return data.decode().replace(str(ROOT), str(live)).replace('/home/andrew/dotfiles', str(live)).encode()
    except UnicodeDecodeError:
        return data


def payload(live):
    result = {}
    for name in VISUAL:
        data = (ROOT/name).read_bytes()
        if name == 'mako/config':
            data = data.decode().replace(str(ROOT), str(live)).encode()
        result[name] = data
    result['quickshell/shell.qml'] = (ROOT/'legacy/deployment/ancient-odyssey/shell.qml').read_bytes()
    for path in (ROOT/'assets/themes/ancient-odyssey').iterdir():
        result[str(path.relative_to(ROOT))] = path.read_bytes()
    result['assets/themes/ancient-odyssey/waybar.css'] = (ROOT/'legacy/deployment/ancient-odyssey/waybar.css').read_bytes()
    for theme in ('catppuccin-mocha', 'gruvbox-dark', 'tokyo-night'):
        name = 'assets/themes/'+theme+'/mako.conf'
        result[name] = (ROOT/name).read_bytes()
    return result


def atomic(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.odyssey-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def restore(folder):
    manifest = json.loads((folder/'manifest.json').read_text())
    live = Path(manifest['live'])
    for item in manifest['files']:
        target = live/item['name']
        allowed = {item['installed_sha256']}
        saved = folder/'files'/item['name']
        if saved.exists():
            allowed.add(digest(saved.read_bytes()))
        if target.exists() and digest(target.read_bytes()) not in allowed:
            raise RuntimeError('File changed after deployment; refusing overwrite: '+str(target))
    for item in reversed(manifest['files']):
        target = live/item['name']
        if item['existed']:
            atomic(target, (folder/'files'/item['name']).read_bytes(), item['mode'])
        elif target.exists():
            target.unlink()
    link = live/'assets/themes/current'
    temp = link.with_name('.rollback-odyssey')
    temp.symlink_to(manifest['theme'])
    os.replace(temp, link)
    for key, value in manifest['gtk'].items():
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', key, value], check=True)
    subprocess.run([str(live/'scripts/wallpaper.sh')], check=True)
    subprocess.run(['makoctl', 'reload'], check=True)
    (live/'alacritty/alacritty.toml').touch()
    print('Restored:', folder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--rollback', type=Path)
    args = parser.parse_args()
    if args.rollback:
        if not args.apply:
            print('Rollback plan:', args.rollback)
            return
        restore(args.rollback)
        return
    live = (Path.home()/'.config/quickshell').resolve().parent
    if not (live/'quickshell/shell.qml').is_file() or (live/'.git').exists():
        raise RuntimeError('Expected installed snapshot, not a checkout')
    if (Path.home()/'.config/niri/config.kdl').resolve() != live/'niri/config.kdl':
        raise RuntimeError('Niri and Quickshell use different snapshots')
    files = payload(live)
    for name in VISUAL+('quickshell/shell.qml',):
        if (live/name).read_bytes() != original(name, live):
            raise RuntimeError('Installed file differs from audited baseline: '+name)
    # Validate the existing config and candidate theme without changing any live link.
    subprocess.run(['niri', 'validate', '-c', str(ROOT/'niri/config.kdl')], check=True)
    print('Target:', live)
    print('Theme:', os.readlink(live/'assets/themes/current'), '-> ancient-odyssey')
    print('Files:', '\n'.join(sorted(files)))
    print('Backend, hardware controls, Niri output/binds and widget state are preserved.')
    if not args.apply:
        return
    folder = Path.home()/'.local/state/dotfiles/theme-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    folder.mkdir(parents=True, mode=0o700)
    manifest = dict(live=str(live), theme=os.readlink(live/'assets/themes/current'), files=[], gtk={})
    for key in ('gtk-theme','color-scheme'):
        manifest['gtk'][key] = subprocess.check_output(['gsettings','get','org.gnome.desktop.interface',key],text=True).strip()
    for name, data in files.items():
        target = live/name
        existed = target.exists()
        mode = target.stat().st_mode & 0o777 if existed else 0o755 if name.endswith('.sh') else 0o644
        if existed:
            saved = folder/'files'/name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        manifest['files'].append(dict(name=name, existed=existed, mode=mode, installed_sha256=digest(data)))
    state = Path.home()/'.local/state/niri-shell/widgets.json'
    before = state.read_bytes() if state.exists() else None
    if before is not None:
        atomic(folder/'widgets.json', before, 0o600)
    atomic(folder/'manifest.json', json.dumps(manifest,indent=2).encode(),0o600)
    print('Backup:', folder, flush=True)
    try:
        # Theme assets are installed before the QML change triggers a hot reload.
        for name in sorted(files, key=lambda n: (n.startswith('quickshell/'), n)):
            atomic(live/name, files[name], next(i['mode'] for i in manifest['files'] if i['name']==name))
        subprocess.run([str(live/'scripts/theme-switcher.sh'), 'ancient-odyssey'],check=True)
        if before is not None and state.read_bytes() != before:
            raise RuntimeError('Widget settings changed during theme deployment')
        subprocess.run(['niri','validate','-c',str(live/'niri/config.kdl')],check=True)
    except BaseException:
        restore(folder)
        raise
    print('Applied theme only. Rollback:', folder)

if __name__ == '__main__':
    main()
