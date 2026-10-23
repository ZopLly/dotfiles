#!/usr/bin/env python3
"""Apply the audited Quickshell update to the existing themed snapshot; default: plan."""
import argparse
import ast
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REVISION = 'odyssey-control-center-v3'
spec = importlib.util.spec_from_file_location('theme_deploy', ROOT/'scripts/apply-odyssey.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def run(args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, timeout=10, **kwargs)


def ipc(live, method):
    result = run(['qs', 'ipc', '-p', str(live/'quickshell'), 'call', 'shell', method])
    if result.returncode:
        raise RuntimeError('Quickshell IPC unavailable: '+result.stderr.strip())
    return json.loads(result.stdout)


def process_count(live, backend=False):
    expected = str(live/'quickshell/backend.py' if backend else live/'quickshell')
    result = run(['ps', '-eo', 'comm=,args='])
    count = 0
    for line in result.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        command, args = parts
        if backend:
            count += command in ('python3','python') and expected in args.split()
        else:
            count += command in ('qs','quickshell') and expected in args.split()
    return count


def stop(live):
    result = run(['qs', 'kill', '-p', str(live/'quickshell')])
    if result.returncode and process_count(live):
        raise RuntimeError('Could not stop the selected Quickshell')
    deadline = time.monotonic()+8
    while time.monotonic() < deadline:
        if process_count(live) == 0 and process_count(live, backend=True) == 0:
            return
        time.sleep(.2)
    raise RuntimeError('Selected shell/backend did not stop; refusing duplicate launch')


def start(live, expected_revision=None):
    if process_count(live) or process_count(live, backend=True):
        raise RuntimeError('An instance is already running')
    result = run(['qs', '-d', '-n', '-p', str(live/'quickshell')])
    if result.returncode:
        raise RuntimeError('Quickshell failed to launch: '+result.stderr.strip())
    deadline = time.monotonic()+20
    while time.monotonic() < deadline:
        try:
            status = ipc(live, 'systemStatus' if expected_revision else 'status')
            if expected_revision and status.get('revision') != expected_revision:
                time.sleep(.3)
                continue
            if expected_revision and status.get('error'):
                raise RuntimeError(status['error'])
            if process_count(live) == 1 and process_count(live, backend=True) == 1:
                return status
        except (RuntimeError, ValueError):
            pass
        time.sleep(.3)
    raise RuntimeError('Quickshell/backend readiness check failed')


def baseline(name, live, ref='8180586'):
    result = subprocess.run(['git', '-C', str(ROOT), 'show', ref+':'+name], capture_output=True)
    if result.returncode:
        return None
    return result.stdout.replace(str(ROOT).encode(), str(live).encode())


def deployed_hashes(live):
    hashes = {}
    history = Path.home()/'.local/state/dotfiles/shell-backups'
    for path in history.glob('*/manifest.json'):
        try:
            manifest = json.loads(path.read_text())
            if manifest.get('live') != str(live):
                continue
            for item in manifest['files']:
                hashes.setdefault(item['name'], set()).add(item['sha256'])
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return hashes


def payload(live):
    result = {}
    themed = helpers.payload(live)
    deployed = deployed_hashes(live)
    for path in sorted((ROOT/'quickshell').iterdir()):
        if not path.is_file() or path.suffix not in ('.qml','.py','.js','.sh'):
            continue
        name = str(path.relative_to(ROOT))
        data = path.read_bytes()
        if path.suffix == '.py':
            ast.parse(data.decode())
        target = live/name
        if target.exists():
            previous = target.read_bytes()
            if previous == data:
                continue
            expected = {candidate for candidate in (themed.get(name), baseline(name, live), baseline(name, live, '50983aa')) if candidate is not None}
            if previous not in expected and helpers.digest(previous) not in deployed.get(name, set()):
                raise RuntimeError('Installed file changed since audit: '+name)
        result[name] = data
    return result


def restore(folder):
    manifest = json.loads((folder/'manifest.json').read_text())
    live = Path(manifest['live'])
    for item in manifest['files']:
        target = live/item['name']
        saved = folder/'files'/item['name']
        allowed = {item['sha256']}
        if saved.exists():
            allowed.add(helpers.digest(saved.read_bytes()))
        if target.exists() and helpers.digest(target.read_bytes()) not in allowed:
            raise RuntimeError('File edited after update: '+str(target))
    stop(live)
    for item in manifest['files']:
        target = live/item['name']
        if item['existed']:
            helpers.atomic(target, (folder/'files'/item['name']).read_bytes(), item['mode'])
        elif target.exists():
            target.unlink()
    start(live, manifest.get('previous_revision'))
    print('Restored shell files; widget settings were not overwritten:', folder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--rollback', type=Path)
    args = parser.parse_args()
    if args.rollback:
        if args.apply:
            restore(args.rollback)
        else:
            print('Would restore:', args.rollback)
        return
    live = (Path.home()/'.config/quickshell').resolve().parent
    if (live/'.git').exists() or not (live/'quickshell/shell.qml').exists():
        raise RuntimeError('Expected an installed snapshot')
    if (Path.home()/'.config/niri/config.kdl').resolve() != live/'niri/config.kdl':
        raise RuntimeError('Niri and Quickshell snapshots differ')
    files = payload(live)
    print('Target:', live)
    print('Changed files:', '\n'.join(files))
    print('Preserved: theme, Niri configuration, services, network/audio state, widgets.json')
    if not args.apply:
        return
    for name in ('qs','niri','nmcli','bluetoothctl','wpctl','pactl','brightnessctl','dbus-monitor'):
        if not shutil.which(name):
            raise RuntimeError('Missing dependency: '+name)
    subprocess.run(['niri','validate','-c',str(ROOT/'niri/config.kdl')],check=True)
    current = ipc(live, 'status')
    if current.get('edit'):
        raise RuntimeError('Widget editing is active; finish dragging before updating')
    if process_count(live) != 1 or process_count(live, backend=True) != 1:
        raise RuntimeError('Expected exactly one active shell and backend')
    state = Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'niri-shell/widgets.json'
    before = state.read_bytes() if state.exists() else None
    folder = Path.home()/'.local/state/dotfiles/shell-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    folder.mkdir(parents=True, mode=0o700)
    previous_system = ipc(live, 'systemStatus')
    manifest = dict(live=str(live), files=[], previous_revision=previous_system.get('revision'))
    for name,data in files.items():
        target = live/name
        existed = target.exists()
        mode = target.stat().st_mode & 0o777 if existed else 0o644
        if existed:
            saved = folder/'files'/name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target,saved)
        manifest['files'].append(dict(name=name,existed=existed,mode=mode,sha256=helpers.digest(data)))
    helpers.atomic(folder/'manifest.json',json.dumps(manifest,indent=2).encode(),0o600)
    if before is not None:
        helpers.atomic(folder/'widgets.json',before,0o600)
    print('Backup:',folder,flush=True)
    stopped = False
    try:
        stop(live)
        stopped = True
        for name,data in files.items():
            helpers.atomic(live/name,data,next(i['mode'] for i in manifest['files'] if i['name']==name))
        result = start(live,EXPECTED_REVISION)
        if before is not None and state.read_bytes() != before:
            raise RuntimeError('Saved widget settings changed during update')
        (folder/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print('Verified live state:',json.dumps(result,ensure_ascii=False),flush=True)
        print('Shell instances: 1; backend processes: 1; widget file unchanged')
    except BaseException:
        if stopped:
            restore(folder)
        raise
    print('Applied. Rollback:',folder)

if __name__=='__main__':
    main()
