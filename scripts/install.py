#!/usr/bin/env python3
"""Install an immutable-path snapshot; default invocation only prints the plan."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('alacritty', 'fuzzel', 'mako', 'gtklock', 'quickshell')
LEGACY_COMPONENTS = ('waybar', 'eww')
SOURCES = COMPONENTS + ('niri', 'assets', 'scripts', 'session', 'systemd')
DEPENDENCIES = ('niri', 'bash', 'jq', 'alacritty', 'fuzzel',
                'mako', 'gtklock', 'swayidle', 'awww', 'awww-daemon', 'magick',
                'playerctl', 'wpctl', 'pamixer', 'brightnessctl', 'cava', 'curl',
                'notify-send', 'gdbus', 'gsettings', 'pavucontrol',
                'nm-connection-editor', 'blueman-manager', 'nmcli', 'bluetoothctl', 'pactl', 'dbus-monitor', 'qs', 'gcc', 'pkg-config')

def exists(path):
    return path.exists() or path.is_symlink()

def rollback(manifest):
    data = json.loads(manifest.read_text())
    # Do not overwrite changes made after installation.
    for item in data:
        target = Path(item['target'])
        if not target.is_symlink() or str(target.readlink()) != item['source']:
            raise RuntimeError(f'Target changed since installation: {target}')
    for item in reversed(data):
        target = Path(item['target'])
        target.unlink()
        backup = Path(item['backup'])
        if exists(backup):
            backup.rename(target)
    manifest.rename(manifest.with_suffix('.restored.json'))
    subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True,check=False)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shell', choices=('quickshell', 'legacy'), default='quickshell', help='Choose the new shell or previous Waybar/Eww setup')
    parser.add_argument('--portable', action='store_true', help='Use automatic monitor setup and native shell bindings on a new computer')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--stage-only', action='store_true', help='Build and validate a snapshot without installing it')
    parser.add_argument('--rollback', type=Path, metavar='MANIFEST')
    args = parser.parse_args()
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))).absolute()
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'dotfiles'
    state = state.absolute()
    if args.rollback:
        if not args.apply:
            print(f'Would restore backups from {args.rollback}. Add --apply to execute.')
        else:
            rollback(args.rollback)
        return
    components = COMPONENTS + (LEGACY_COMPONENTS if args.shell == 'legacy' else ())
    print('Snapshot source:', ROOT)
    print('Config destination:', config)
    print('Components:', ', '.join(components + ('niri',)))
    print('Existing directories will be backed up; their extra files are retained in the snapshot.')
    print('swayidle.service will be installed, but not enabled or restarted automatically.')
    required=DEPENDENCIES + (('waybar','eww','gsimplecal') if args.shell=='legacy' else ())
    missing = [name for name in required if not shutil.which(name)]
    if missing:
        print('Missing dependencies:', ', '.join(missing))
        if args.apply or args.stage_only:
            raise RuntimeError('Install missing dependencies before proceeding.')
    if not args.apply and not args.stage_only:
        print('Preview only. No files changed.')
        return
    if not (ROOT/'niri/conf.d/binds.kdl').is_file() or not (ROOT/'niri/runtime.sh').is_file():
        raise RuntimeError('Incomplete modular Niri configuration')
    subprocess.run(['niri', 'validate', '-c', str(ROOT / 'niri/config.kdl')], check=True)
    subprocess.run(['bash', str(ROOT/'gtklock/modules/build.sh')], check=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    release = state / 'releases' / stamp
    backup = state / 'backups' / stamp
    release.mkdir(parents=True)
    backup.mkdir(parents=True)
    for name in SOURCES:
        dest = release / name
        # Preserve application-specific files that are not managed by this repository.
        if name in components + ('niri',) and (config / name).is_dir():
            shutil.copytree(config / name, dest, symlinks=True)
        # Overlay safely: never write through a copied pre-existing symlink.
        for source in (ROOT / name).rglob('*'):
            if '__pycache__' in source.parts or 'backups' in source.relative_to(ROOT).parts or source.suffix == '.pyc':
                continue
            target = dest / source.relative_to(ROOT / name)
            if source.is_dir() and not source.is_symlink():
                if target.is_symlink():
                    target.unlink()
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if exists(target):
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            if source.is_symlink():
                target.symlink_to(source.readlink())
            else:
                shutil.copy2(source, target)
    # Expand legacy runtime paths into this snapshot. Repository files remain untouched.
    for name in SOURCES:
        for source in (ROOT / name).rglob('*'):
            if '__pycache__' in source.parts or 'backups' in source.relative_to(ROOT).parts or source.suffix == '.pyc':
                continue
            if not source.is_file() or source.is_symlink():
                continue
            try:
                text = source.read_text()
            except UnicodeError:
                continue
            text = text.replace(str(ROOT), str(release)).replace('/home/andrew/dotfiles', str(release)).replace('~/dotfiles', str(release))
            text = text.replace('~/.config', str(config)).replace('/home/andrew/.config', str(config))
            (release / source.relative_to(ROOT)).write_text(text)
    # Authorize the installed snapshot for native panel actions, never the source checkout.
    marker=release/'.shell-release.json'
    marker.write_text(json.dumps(dict(schema=1,root=str(release.resolve()),state=str(Path.home()/'.local/state/niri-shell'))))
    marker.chmod(0o600)
    # Terminal palette imports must follow this snapshot; source inline colours cannot win.
    import re
    profile=(release/'alacritty/alacritty.toml').read_text()
    imports=[str(release/'assets/themes/current/alacritty.toml'),str(release/'alacritty/opacity.toml')]
    profile=re.sub(r'\[general\]\s*\nimport\s*=\s*\[[^\]]*\]','[general]\nimport = '+json.dumps(imports),profile,count=1)
    profile=re.sub(r'(?ms)^\[colors(?:\.[^\]]*)?\].*?(?=^\[|\Z)','',profile)
    (release/'alacritty/niri.toml').write_text(profile)
    if args.portable:
        if config!=Path.home()/'.config' or state!=Path.home()/'.local/state/dotfiles':
            raise RuntimeError('Portable native shell currently requires default XDG config/state paths')
        # Hardware-specific output coordinates from the author's laptop are not portable.
        existing=config/'niri/conf.d/outputs.kdl'
        (release/'niri/conf.d/outputs.kdl').write_text(existing.read_text() if existing.is_file() else '// Outputs are detected automatically.\n')
    (release/'systemd/user/swayidle.service').write_text((release/'systemd/user/swayidle.service').read_text().replace('/home/andrew/',str(Path.home())+'/'))
    if args.shell == 'legacy':
        for name in LEGACY_COMPONENTS:
            shutil.copytree(ROOT/'legacy'/name, release/name, symlinks=False)
        for name in LEGACY_COMPONENTS:
            for source in (release/name).rglob('*'):
                if source.is_file() and source.suffix in ('.sh','.py','.css','.scss','.yuck','.jsonc'):
                    text=source.read_text().replace(str(ROOT),str(release)).replace('/home/andrew/dotfiles',str(release))
                    source.write_text(text)
        legacy_config=(ROOT/'legacy/niri/config.kdl').read_text().replace(str(ROOT),str(release))
        (release/'niri/config.kdl').write_text(legacy_config)
    subprocess.run(['niri', 'validate', '-c', str(release / 'niri/config.kdl')], check=True)
    # Reject broken managed symlinks before touching any installed configuration.
    for name in SOURCES:
        for source in (ROOT/name).rglob('*'):
            target = release/source.relative_to(ROOT)
            if source.is_symlink() and not target.exists():
                raise RuntimeError(f'Broken snapshot link: {target}')
    if args.stage_only:
        print('Validated snapshot (not installed):', release)
        return
    targets = [(config / name, release / name) for name in components]
    targets.append((config / 'systemd/user/swayidle.service', release / 'systemd/user/swayidle.service'))
    targets.append((config / 'niri', release / 'niri'))
    journal = []
    manifest = backup / 'manifest.json'
    try:
        for i, (target, source) in enumerate(targets):
            target.parent.mkdir(parents=True, exist_ok=True)
            saved = backup / str(i)
            if exists(target):
                target.rename(saved)
            try:
                target.symlink_to(source)
            except BaseException:
                if exists(saved):
                    saved.rename(target)
                raise
            journal.append(dict(target=str(target), source=str(source), backup=str(saved)))
            manifest.write_text(json.dumps(journal, indent=2))
    except BaseException:
        if manifest.exists():
            rollback(manifest)
        raise
    print('Installed snapshot:', release)
    print('Rollback manifest:', manifest)
    subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True,check=False)
    print('No services were restarted. Re-enter the session after reviewing the installation.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
