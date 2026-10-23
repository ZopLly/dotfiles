#!/usr/bin/env python3
"""Save a stable app layout and offer to restore it once per Niri login."""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state'))) / 'niri-session'
COMMANDS = {'alacritty': ['alacritty'], 'firefox': ['firefox'], 'spotify': ['spotify']}
STOP = threading.Event()
SHUTTING_DOWN = threading.Event()


def call(args):
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=5).stdout


def query(kind):
    return json.loads(call(['niri', 'msg', '-j', kind]))


def capture():
    spaces = {w['id']: w for w in query('workspaces')}
    entries = []
    for window in query('windows'):
        app = (window.get('app_id') or '').lower()
        workspace = spaces.get(window.get('workspace_id'))
        if app not in COMMANDS or not workspace:
            continue
        pos = window.get('layout', {}).get('pos_in_scrolling_layout')
        entries.append(dict(app_id=app, workspace=workspace.get('name') or str(workspace['idx']),
                            output=workspace.get('output'), column=pos[0] if pos else None))
    return {'version': 2, 'windows': sorted(entries, key=lambda w: (w['output'] or '', w['workspace'], w['column'] or 0, w['app_id']))}


def save(data):
    temp = STATE/'session.tmp'
    temp.write_text(json.dumps(data, indent=2))
    temp.chmod(0o600)
    temp.replace(STATE/'session.json')


def restore(data):
    used = set()
    for entry in data.get('windows', []):
        app = str(entry.get('app_id', '')).lower()
        if app not in COMMANDS:
            continue
        try:
            windows = query('windows')
            matches = [w for w in windows if (w.get('app_id') or '').lower() == app and w['id'] not in used]
            window = matches[0] if matches else None
            if window is None:
                old = {w['id'] for w in windows}
                command = COMMANDS[app][:]
                if app == 'firefox' and any((w.get('app_id') or '').lower() == app for w in windows):
                    command.append('--new-window')
                call(['niri', 'msg', 'action', 'spawn', '--', *command])
                for _ in range(80):
                    if STOP.wait(.25):
                        return
                    candidates = [w for w in query('windows') if w['id'] not in old and (w.get('app_id') or '').lower() == app]
                    if candidates:
                        window = candidates[0]
                        break
            if window is None:
                print(f'No window appeared for {app}', flush=True)
                continue
            used.add(window['id'])
            wid = str(window['id'])
            if entry.get('output') in query('outputs'):
                call(['niri', 'msg', 'action', 'move-window-to-monitor', '--id', wid, entry['output']])
            call(['niri', 'msg', 'action', 'move-window-to-workspace', '--window-id', wid, '--focus', 'false', str(entry['workspace'])])
            if entry.get('column') is None:
                call(['niri', 'msg', 'action', 'move-window-to-floating', '--id', wid])
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            print(f'Could not restore {app}: {exc}', flush=True)


def watch_shutdown(process):
    for line in process.stdout:
        if 'PrepareForShutdown' in line:
            if 'true' in line:
                SHUTTING_DOWN.set()
            elif 'false' in line:
                SHUTTING_DOWN.clear()


def main():
    if os.environ.get('NIRI_SHELL_PREVIEW') == '1':
        return
    STATE.mkdir(parents=True, exist_ok=True)
    lock = (STATE/'manager.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    monitor = subprocess.Popen(['gdbus', 'monitor', '--system', '--dest', 'org.freedesktop.login1', '--object-path', '/org/freedesktop/login1'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    threading.Thread(target=watch_shutdown, args=(monitor,), daemon=True).start()
    try:
        # Wait for Niri IPC and the initial output configuration.
        for _ in range(40):
            try:
                query('workspaces')
                break
            except (OSError, ValueError, subprocess.SubprocessError):
                if STOP.wait(.25):
                    return
        try:
            data = json.loads((STATE/'session.json').read_text())
            if data.get('version') == 2 and data.get('windows'):
                choice = subprocess.run(['fuzzel', '--dmenu', '--prompt=Session: '], input='Restore previous session\nStart fresh\n', text=True, capture_output=True)
                if choice.returncode == 0 and choice.stdout.strip() == 'Restore previous session':
                    restore(data)
                elif choice.returncode == 0 and choice.stdout.strip() == 'Start fresh':
                    # Preserve the previous snapshot as a backup before clearing it.
                    (STATE/'session.json').replace(STATE/'previous-session.json')
        except (OSError, ValueError, AttributeError) as exc:
            print(f'Session prompt: {exc}', flush=True)
        candidate, saved, since = None, None, time.monotonic()
        while not STOP.is_set():
            if SHUTTING_DOWN.is_set():
                candidate, since = None, time.monotonic()
                STOP.wait(.5)
                continue
            try:
                current = capture()
                if current != candidate:
                    candidate, since = current, time.monotonic()
                # Keep the last nonempty layout; ignore transient shutdown window closures.
                if current['windows'] and current != saved and time.monotonic()-since >= 15 and not STOP.is_set() and not SHUTTING_DOWN.is_set():
                    save(current)
                    saved = current
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                print(f'Session save: {exc}', flush=True)
            STOP.wait(3)
    finally:
        monitor.terminate()
        monitor.wait(timeout=5)


if __name__ == '__main__':
    main()
