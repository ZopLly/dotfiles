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
import tempfile

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

def runtime_text(text, release, config):
    prefixes = {str(ROOT), '/home/andrew/dotfiles/niri-staging',
                '/home/andrew/dotfiles', '~/dotfiles/niri-staging', '~/dotfiles'}
    for prefix in sorted(prefixes, key=len, reverse=True):
        text = text.replace(prefix, str(release))
    return text.replace('~/.config', str(config)).replace('/home/andrew/.config', str(config))

def write_manifest(path, data):
    # Publish a complete recovery plan before moving the first configuration.
    fd, temporary = tempfile.mkstemp(prefix='.manifest-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def restore_links(data, allow_pending=False):
    actions = []
    # Preflight every target before restoring any of them.
    for item in data:
        target, saved = Path(item['target']), Path(item['backup'])
        linked = target.is_symlink() and str(target.readlink()) == item['source']
        pending = allow_pending or item.get('installed') is False
        if linked:
            if item.get('existed') and not exists(saved):
                raise RuntimeError(f'Missing backup: {saved}')
            actions.append((target, saved, True))
        elif pending and not exists(target) and exists(saved):
            actions.append((target, saved, False))
        elif pending and not exists(saved):
            continue  # This entry has not been touched yet.
        else:
            raise RuntimeError(f'Target changed since installation: {target}')
    for target, saved, linked in reversed(actions):
        if linked:
            target.unlink()
        if exists(saved):
            saved.rename(target)

def rollback(manifest):
    restore_links(json.loads(manifest.read_text()))
    manifest.rename(manifest.with_suffix('.restored.json'))
    subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True,check=False)

def install_links(targets, backup):
    manifest = backup / 'manifest.json'
    journal = [dict(target=str(target), source=str(source), backup=str(backup/str(i)),
                    existed=exists(target), installed=False)
               for i, (target, source) in enumerate(targets)]
    write_manifest(manifest, journal)
    try:
        for item in journal:
            target = Path(item['target'])
            target.parent.mkdir(parents=True, exist_ok=True)
            if item['existed']:
                target.rename(item['backup'])
            target.symlink_to(item['source'])
            item['installed'] = True
        write_manifest(manifest, journal)
    except BaseException:
        restore_links(journal, allow_pending=True)
        manifest.rename(manifest.with_suffix('.restored.json'))
        raise
    return manifest

def isolated_check(args):
    # Build a relocated source tree under a disposable HOME, never the user's config.
    with tempfile.TemporaryDirectory(prefix='niri-shell-check-') as folder:
        scratch = Path(folder)
        source = scratch/'source'
        source.mkdir()
        names = SOURCES + (('legacy',) if args.shell == 'legacy' else ())
        for name in names:
            shutil.copytree(ROOT/name, source/name, symlinks=True,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.so', 'backups'))
        home = scratch/'home'
        home.mkdir()
        env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home/'.config'),
                   XDG_STATE_HOME=str(home/'.local/state'), XDG_CACHE_HOME=str(home/'.cache'))
        command = [sys.executable, str(source/'scripts/install.py'), '--stage-only', '--shell', args.shell]
        if args.portable:
            command.append('--portable')
        subprocess.run(command, env=env, check=True)
    print('Check passed: relocated snapshot built and validated; installed configuration unchanged.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shell', choices=('quickshell', 'legacy'), default='quickshell', help='Choose the new shell or previous Waybar/Eww setup')
    parser.add_argument('--portable', action='store_true', help='Use automatic monitor setup and native shell bindings on a new computer')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true', help='Build and validate in a disposable HOME without installing')
    mode.add_argument('--stage-only', action='store_true', help='Build and validate a snapshot without installing it')
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
        if args.apply or args.stage_only or args.check:
            raise RuntimeError('Install missing dependencies before proceeding.')
    if args.check:
        isolated_check(args)
        return
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
            text = runtime_text(text, release, config)
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
                    text=runtime_text(source.read_text(), release, config)
                    source.write_text(text)
        legacy_config=runtime_text((ROOT/'legacy/niri/config.kdl').read_text(), release, config)
        (release/'niri/config.kdl').write_text(legacy_config)
    subprocess.run(['niri', 'validate', '-c', str(release / 'niri/config.kdl')], check=True)
    # Reject broken managed symlinks before touching any installed configuration.
    for name in SOURCES:
        for source in (ROOT/name).rglob('*'):
            target = release/source.relative_to(ROOT)
            if source.is_symlink() and not target.exists():
                raise RuntimeError(f'Broken snapshot link: {target}')
    for relative, theme in (('mako/config', 'mako.conf'), ('fuzzel/fuzzel.ini', 'fuzzel.ini')):
        expected = release/'assets/themes/current'/theme
        includes = [line.split('=', 1)[1].strip() for line in (release/relative).read_text().splitlines()
                    if line.strip().startswith('include=')]
        if str(expected) not in includes or not expected.is_file():
            raise RuntimeError(f'Invalid theme include in {relative}: expected {expected}')
    if args.stage_only:
        print('Validated snapshot (not installed):', release)
        return
    targets = [(config / name, release / name) for name in components]
    targets.append((config / 'systemd/user/swayidle.service', release / 'systemd/user/swayidle.service'))
    targets.append((config / 'niri', release / 'niri'))
    manifest = install_links(targets, backup)
    print('Installed snapshot:', release)
    print('Rollback manifest:', manifest)
    subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True,check=False)
    print('No services were restarted. Re-enter the session after reviewing the installation.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
