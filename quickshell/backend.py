#!/usr/bin/env python3
"""JSON-lines bridge for the desktop shell. Never reads connection secrets."""
import atexit
import signal
import json
import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import sys
import threading
import time
import queue
import math
import tempfile

# Also support tests loading this file by absolute path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from system_state import wifi_state, audio_state, audio_levels, audio_devices, bluetooth_state, brightness, backlight_signature, battery_level
from state_cache import StateCache, action_scopes, event_scopes

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = os.environ.get('NIRI_SHELL_PREVIEW') == '1'
STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state'))) / 'niri-shell/widgets.json'
PALETTE = ROOT/'assets/themes/current/waybar.css'
EVENT_PROCESSES = []
CACHE = StateCache()
TASK_LOCK = threading.Lock()
TASKS = {}
OPERATIONS = {}

def start_task(group, name, command, target=''):
    with TASK_LOCK:
        if group in TASKS:
            raise RuntimeError('Операция уже выполняется')
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        TASKS[group] = dict(process=process, name=name, target=target, started=time.monotonic())
        OPERATIONS[group] = dict(busy=True, action=name, target=target, error='')


def poll_tasks():
    completed = []
    with TASK_LOCK:
        for group, task in list(TASKS.items()):
            proc = task['process']
            if group == 'bluetooth' and time.monotonic()-task['started'] > 45 and proc.poll() is None:
                proc.terminate()
            if proc.poll() is not None:
                completed.append((group, TASKS.pop(group)))
    for group, task in completed:
        proc = task['process']
        _, stderr = proc.communicate(timeout=1)
        error = stderr.decode(errors='replace').strip()[:400] if proc.returncode else ''
        if proc.returncode and not error:
            error = 'Операция не завершена; проверьте устройство или окно подтверждения'
        if group == 'bluetooth' and task['name'] in ('bluetooth-pair', 'bluetooth-device') and not error:
            devices = bluetooth_state(optional)['bluetooth_devices']
            device = next((d for d in devices if d['address'] == task['target']), {})
            field = 'paired' if task['name'] == 'bluetooth-pair' else 'connected'
            expected = task.get('enabled', True)
            if bool(device.get(field)) != expected:
                error = 'Действие не подтверждено устройством. Для PIN откройте Blueman.'
        with TASK_LOCK:
            OPERATIONS[group] = dict(busy=False, action=task['name'], target=task['target'], error=error)
        CACHE.invalidate(action_scopes(task['name']))
    return bool(completed)


def operation_state():
    with TASK_LOCK:
        return {group: dict(value) for group, value in OPERATIONS.items()}


def cleanup():
    with TASK_LOCK:
        bluetooth_task = TASKS.get('bluetooth')
    if bluetooth_task and bluetooth_task['process'].poll() is None:
        bluetooth_task['process'].terminate()
        try: bluetooth_task['process'].wait(timeout=1)
        except subprocess.TimeoutExpired:
            bluetooth_task['process'].kill(); bluetooth_task['process'].wait()
    for process in list(EVENT_PROCESSES):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

atexit.register(cleanup)

DEFAULT_COLORS = dict(bg='#1e1e2e', fg='#cdd6f4', fg_dim='#6c7086', bg_modules='#11111b', accent='#89b4fa', power_color='#f38ba8')


def run(args, timeout=3):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=dict(os.environ, LC_ALL="C"))
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or f'{args[0]}: команда не выполнена')
    return p.stdout.strip()


def optional(args, default=''):
    try:
        return run(args)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return default


def layout_load():
    try:
        result = json.loads(STATE.read_text())
        if not isinstance(result, dict):
            return {}
        if result.get('_version') != 2:
            for output, widgets in list(result.items()):
                if not output.startswith('_') and isinstance(widgets, dict):
                    result[output] = {'workspaces': {'index:1': widgets}}
            result['_version'] = 2
        return result
    except (OSError, ValueError):
        return {}


PANEL_DEFAULTS = {'center': ['calendar', 'media'], 'right': ['connectivity', 'vpn', 'audio', 'brightness', 'power', 'desktop']}
PANEL_MODULES = {'weather', 'calendar', 'media', 'connectivity', 'vpn', 'audio', 'brightness', 'power', 'desktop'}


def panel_layouts():
    saved = layout_load().get('_panels', {})
    if not isinstance(saved, dict):
        saved = {}
    result = {}
    for panel, default in PANEL_DEFAULTS.items():
        values = saved.get(panel, default)
        if not isinstance(values, list) or any(not isinstance(v, str) or v not in PANEL_MODULES for v in values) or len(set(values)) != len(values):
            values = default
        result[panel] = values
    return result


def write_layout(data):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        backup = STATE.with_suffix('.json.bak')
        if not backup.exists():
            shutil.copy2(STATE, backup)
            backup.chmod(0o600)
    fd, name = tempfile.mkstemp(prefix='.widgets-', dir=STATE.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, STATE)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save_panel(args):
    panel, modules = args.get('panel'), args.get('modules')
    if panel not in PANEL_DEFAULTS or not isinstance(modules, list) or len(modules) > len(PANEL_MODULES):
        raise ValueError('Invalid panel layout')
    if any(not isinstance(m, str) or m not in PANEL_MODULES for m in modules) or len(set(modules)) != len(modules):
        raise ValueError('Unknown or duplicate module')
    data = layout_load()
    data['_version'] = 2
    if not isinstance(data.get('_panels'), dict):
        data['_panels'] = {}
    data['_panels'][panel] = modules
    write_layout(data)


def save_widget(args):
    output, name = str(args['output'])[:100], args['id']
    workspace = str(args.get('workspace', 'index:1'))[:200]
    if name not in ('clock', 'media', 'weather', 'metrics') or not workspace.startswith(('index:', 'name:')):
        raise ValueError('Unknown widget or workspace')
    data = layout_load()
    data['_version'] = 2
    widgets = data.setdefault(output, {}).setdefault('workspaces', {}).setdefault(workspace, {})
    defaults = dict(x=.65 if name in ("weather", "metrics") else .08, y=.22 if name == 'clock' else .78 if name == "metrics" else .55, width=320, height=180, visible=True)
    defaults.update(widgets.get(name, {}))
    defaults.update({key: args[key] for key in defaults if key in args})
    if any(not math.isfinite(float(defaults[key])) for key in ('x', 'y', 'width', 'height')):
        raise ValueError('Invalid widget coordinates')
    values = {key: max(0., min(1., float(defaults[key]))) for key in ('x', 'y')}
    values['width'] = max(220, min(520, int(defaults['width'])))
    values['height'] = max(150, min(420, int(defaults['height'])))
    values['visible'] = bool(defaults['visible'])
    widgets[name] = values
    write_layout(data)


from battery_time import estimate as estimate_battery_time

def battery():
    for path in Path('/sys/class/power_supply').glob('*'):
        try:
            if (path/'type').read_text().strip() == 'Battery':
                percent, status = int((path/'capacity').read_text()), (path/'status').read_text().strip()
                return dict(percent=percent, status=status, level=battery_level(percent, status), **estimate_battery_time(path, status))
        except (OSError, ValueError):
            pass
    return dict(percent=-1, status='Нет батареи', level='unavailable')


def read_palette():
    colors = dict(DEFAULT_COLORS)
    try:
        palette = PALETTE.read_text()
        colors.update(dict(re.findall(r'@define-color\s+(\w+)\s+(#[\da-fA-F]+)', palette)))
        for key, r, g, b, alpha in re.findall(r'@define-color\s+(\w+)\s+rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', palette):
            colors[key] = '#%02x%02x%02x%02x' % (round(float(alpha)*255), int(r), int(g), int(b))
    except OSError:
        pass
    return colors


def niri_state():
    workspaces = json.loads(optional(['niri', 'msg', '-j', 'workspaces'], '[]'))
    layouts = json.loads(optional(['niri', 'msg', '-j', 'keyboard-layouts'], '{}'))
    focused = json.loads(optional(['niri', 'msg', '-j', 'focused-window'], 'null'))
    return dict(window_title=(focused or {}).get('title', ''),
                workspaces=sorted(workspaces, key=lambda w: (w.get('output') or '', w.get('idx', 0))),
                language=(layouts.get('names', [''])[layouts.get('current_idx', 0)] if layouts.get('names') else ''))


def vpn_state():
    active = optional(['nmcli', '-t', '--escape', 'no', '-f', 'NAME,TYPE,UUID', 'connection', 'show', '--active'])
    active_ids = {r[2] for line in active.splitlines() if len(r := line.rsplit(':', 2)) == 3}
    profiles = optional(['nmcli', '-t', '--escape', 'no', '-f', 'NAME,TYPE,UUID', 'connection', 'show'])
    return dict(vpns=[dict(name=r[0], uuid=r[2], active=r[2] in active_ids) for line in profiles.splitlines()
                      if len(r := line.rsplit(':', 2)) == 3 and r[1] in ('vpn', 'wireguard')])


def snapshot():
    result = dict(revision='odyssey-control-center-v3', colors=CACHE.get('palette', read_palette, 1),
                  widgets=layout_load(), panels=panel_layouts(), preview=PREVIEW, operations=operation_state(),
                  battery=CACHE.get('battery', battery))
    result.update(CACHE.get('niri', niri_state))
    if PREVIEW:
        result.update(volume=45, muted=False, brightness=70, wifi=True, network='Тестовая сеть', wifi_device='preview0', wifi_connection_state='connected',
                      bluetooth=True, bluetooth_available=True, bluetooth_devices=[dict(address='00:00:00:00:00:01', name='Наушники · пример', connected=True, paired=True, connecting=False, category='Подключённые'), dict(address='00:00:00:00:00:02', name='Мышь · пример', connected=False, paired=True, connecting=False, category='Сопряжённые'), dict(address='00:00:00:00:00:03', name='Клавиатура · пример', connected=False, paired=False, connecting=False, category='Найденные')], wifi_available=True, wifi_connected=True, wifi_signal=65, networks=[dict(ssid='Тестовая сеть', signal=65, bssid='00:00:00:00:00:01', security='WPA2', active=True), dict(ssid='Гостевая сеть · пример', signal=40, bssid='00:00:00:00:00:02', security='', active=False)], mic_volume=60, mic_muted=False, sinks=[dict(name='preview-speaker', label='Динамики · пример', active=True)], sources=[dict(name='preview-mic', label='Микрофон · пример', active=True)], vpns=[], dnd=False, profiles=['power-saver', 'balanced', 'performance'], profile='balanced', available=False)
        return result
    readers = {
        'audio_levels': lambda: audio_levels(optional),
        'audio_devices': lambda: audio_devices(optional),
        'brightness': lambda: dict(brightness=brightness(optional)),
        'wifi': lambda: wifi_state(optional),
        'vpns': vpn_state,
        'bluetooth': lambda: bluetooth_state(optional),
        'dnd': lambda: dict(dnd='do-not-disturb' in optional(['makoctl', 'mode'])),
        'power': lambda: dict(profile=optional(['powerprofilesctl', 'get'])),
        'profiles': lambda: dict(profiles=re.findall(r'^\s*\*?\s*(power-saver|balanced|performance):', optional(['powerprofilesctl', 'list']), re.M)),
    }
    for name, reader in readers.items():
        result.update(CACHE.get(name, reader, 300 if name == 'profiles' else 30))
    pending = result['operations'].get('bluetooth', {})
    result['bluetooth_devices'] = [dict(d, connecting=bool(pending.get('busy') and pending.get('target') == d['address']), category='Подключённые' if d['connected'] else 'Сопряжённые' if d.get('paired') else 'Найденные') for d in result['bluetooth_devices']]
    result['available'] = True
    return result


def palette_signature():
    try:
        stat = PALETTE.stat()
        return stat.st_ino, stat.st_mtime_ns
    except OSError:
        return None


def action(message):
    name, args = message.get('action'), message.get('args', {})
    CACHE.invalidate(action_scopes(name))
    if name == 'save-panel':
        save_panel(args)
        return
    if name == 'grid':
        data = layout_load()
        data['_options'] = {'snap': bool(args.get('enabled'))}
        write_layout(data)
        return
    if name == 'save-widget':
        save_widget(args)
        return
    if name == 'workspace':
        if args.get('output'):
            run(['niri', 'msg', 'action', 'focus-monitor', str(args['output'])])
        run(['niri', 'msg', 'action', 'focus-workspace', str(int(args['index']))])
        return
    if name == 'layout':
        run(['niri', 'msg', 'action', 'switch-layout', 'next'])
        return
    if name == 'launcher':
        command = ['fuzzel', '--launch-prefix=true'] if PREVIEW else ['fuzzel']
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    if PREVIEW:
        raise RuntimeError('В предпросмотре системные действия отключены')
    if name in ('volume', 'mic-volume', 'brightness'):
        minimum = 5 if name == 'brightness' else 0
        value = max(minimum, min(100, int(args.get('value', minimum))))
        command = ['brightnessctl', '--class=backlight', 'set', f'{value}%'] if name == 'brightness' else ['wpctl', 'set-volume', '@DEFAULT_AUDIO_SOURCE@' if name == 'mic-volume' else '@DEFAULT_AUDIO_SINK@', f'{value}%']
        run(command)
        return
    commands = {
        'wifi': ['nmcli', 'radio', 'wifi', 'on' if args.get('enabled') else 'off'],
        'bluetooth': ['bluetoothctl', 'power', 'on' if args.get('enabled') else 'off'],
        'mic-mute': ['wpctl', 'set-mute', '@DEFAULT_AUDIO_SOURCE@', 'toggle'],
        'mute': ['wpctl', 'set-mute', '@DEFAULT_AUDIO_SINK@', 'toggle'],
        'dnd': ['makoctl', 'mode', '-a' if args.get('enabled') else '-r', 'do-not-disturb'],
        'audio-settings': ['pavucontrol'], 'network-settings': ['nm-connection-editor'],
        'bluetooth-settings': ['blueman-manager'],
        'lock': [str(ROOT/'gtklock/scripts/lock.sh')],
        'suspend': ['systemctl', 'suspend'], 'reboot': ['systemctl', 'reboot'], 'poweroff': ['systemctl', 'poweroff'],
    }
    if name == 'wifi-rescan':
        start_task('wifi', name, ['nmcli', '--wait', '15', 'device', 'wifi', 'rescan'])
        return
    if name == 'wifi-disconnect':
        device = wifi_state(optional)['wifi_device']
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+', device):
            raise ValueError('Wi-Fi device unavailable')
        start_task('wifi', name, ['nmcli', '--wait', '15', 'device', 'disconnect', device])
        return
    if name == 'wifi-connect':
        bssid = str(args.get('bssid', ''))
        if not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', bssid):
            raise ValueError('Invalid access point')
        # NM prompts in a terminal; passwords never cross this JSON bridge.
        start_task('wifi', name, ['alacritty', '-e', 'bash', str(ROOT/'quickshell/wifi-connect.sh'), bssid], bssid)
        return
    if name in ('audio-sink', 'audio-source'):
        kind = name.split('-')[1]
        device = args.get('name')
        if device not in {d['name'] for d in audio_state(optional)[kind+'s']}:
            raise ValueError('Audio device disappeared')
        run(['pactl', 'set-default-'+kind, device])
        return
    if name == 'bluetooth-scan':
        start_task('bluetooth', name, ['bluetoothctl', '--timeout', '10', 'scan', 'on'])
        return
    if name in ('bluetooth-device', 'bluetooth-pair'):
        address = str(args.get('address', ''))
        if not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', address):
            raise ValueError('Invalid Bluetooth address')
        if name == 'bluetooth-pair':
            devices = bluetooth_state(optional)['bluetooth_devices']
            if any(d['address'] == address and d.get('paired') for d in devices):
                raise ValueError('Устройство уже сопряжено')
        command = 'pair' if name == 'bluetooth-pair' else 'connect' if args.get('enabled') else 'disconnect'
        start_task('bluetooth', name, ['bluetoothctl', '--timeout', '30', command, address], address)
        with TASK_LOCK:
            TASKS['bluetooth']['enabled'] = True if command == 'pair' else bool(args.get('enabled'))
        return
    if name == 'vpn':
        uuid = str(args.get('uuid', ''))
        if not re.fullmatch(r'[a-fA-F0-9-]{36}', uuid):
            raise ValueError('Invalid connection identifier')
        run(['nmcli', 'connection', 'up' if args.get('enabled') else 'down', 'uuid', uuid], timeout=30)
    elif name == 'profile':
        if args.get('value') not in ('power-saver', 'balanced', 'performance'):
            raise ValueError('Unknown power profile')
        run(['powerprofilesctl', 'set', args['value']])
    elif name in commands:
        if name.endswith('-settings') or name == 'lock':
            subprocess.Popen(commands[name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            run(commands[name])
    else:
        raise ValueError('Unknown action')


def emit(data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def main():
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    dirty, stopping = threading.Event(), threading.Event()
    actions = queue.Queue(maxsize=64)
    output_lock = threading.Lock()
    def publish(data):
        with output_lock:
            emit(data)
    def events(command, stream):
        while not stopping.is_set():
            proc = None
            try:
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        text=True, env=dict(os.environ, LC_ALL='C'))
                EVENT_PROCESSES.append(proc)
                for line in proc.stdout:
                    scopes = event_scopes(stream, line)
                    if scopes:
                        CACHE.invalidate(scopes)
                        dirty.set()
                proc.wait()
            except OSError:
                return
            finally:
                if proc in EVENT_PROCESSES:
                    EVENT_PROCESSES.remove(proc)
            stopping.wait(3)
    def controls():
        while not stopping.is_set():
            try:
                message = actions.get(timeout=.5)
            except queue.Empty:
                continue
            try:
                action(message)
            except Exception as exc:
                group = 'bluetooth' if str(message.get('action', '')).startswith('bluetooth') else 'wifi' if str(message.get('action', '')).startswith('wifi') else None
                if group:
                    with TASK_LOCK:
                        OPERATIONS[group] = dict(OPERATIONS.get(group, {}), busy=group in TASKS, error=str(exc))
                publish(dict(type='error', message=str(exc)))
            finally:
                CACHE.invalidate(action_scopes(message.get('action')))
                dirty.set()
                actions.task_done()
    commands = [(['niri', 'msg', '-j', 'event-stream'], 'niri')]
    if not PREVIEW:
        commands += [(['nmcli', 'monitor'], 'network'), (['pactl', 'subscribe'], 'audio'),
                     (['dbus-monitor', '--system', "type='signal',sender='org.bluez',interface='org.freedesktop.DBus.Properties',path_namespace='/org/bluez'", "type='signal',sender='org.bluez',interface='org.freedesktop.DBus.ObjectManager'"], 'bluetooth'),
                     (['dbus-monitor', '--system', "type='signal',interface='org.freedesktop.DBus.Properties',path_namespace='/org/freedesktop/UPower'",
                       "type='signal',interface='org.freedesktop.DBus.Properties',path='/net/hadess/PowerProfiles'"], 'power'),
                     (['dbus-monitor', '--session', "type='signal',sender='org.freedesktop.Notifications'"], 'dnd')]
    for command, stream in commands:
        threading.Thread(target=events, args=(command, stream), daemon=True).start()
    threading.Thread(target=controls, daemon=True).start()
    deadline, last_emit = 0, 0
    pending, previous = b'', None
    light_signature = backlight_signature()
    theme_signature = palette_signature()
    notified = set()
    try:
        while True:
            now = time.monotonic()
            if poll_tasks():
                dirty.set()
            if not PREVIEW:
                signature = backlight_signature()
                if signature != light_signature:
                    light_signature = signature
                    CACHE.invalidate({'brightness'})
                    dirty.set()
            palette = palette_signature()
            if palette != theme_signature:
                theme_signature = palette
                CACHE.invalidate({'palette'})
                dirty.set()
            if (now >= deadline or dirty.is_set()) and now-last_emit >= .25:
                dirty.clear()
                try:
                    state = snapshot()
                    if state != previous:
                        publish(dict(type='state', data=state))
                    if previous and not PREVIEW:
                        for key in ('volume', 'muted', 'mic_volume', 'mic_muted', 'brightness'):
                            if state.get(key) != previous.get(key) and state.get(key, -1) != -1:
                                publish(dict(type='osd', data=dict(kind=key, value=state.get(key))))
                    level = state['battery'].get('level')
                    if level not in ('low', 'critical'):
                        notified.clear()
                    elif level not in notified and not PREVIEW:
                        optional(['notify-send', '-a', 'Niri Shell', '-u', 'critical' if level == 'critical' else 'normal',
                                  'Низкий заряд батареи', str(state['battery']['percent'])+'%'])
                        notified.add(level)
                    previous = state
                except Exception as exc:
                    publish(dict(type='error', message=str(exc)))
                last_emit = time.monotonic()
                deadline = last_emit + 30
            readable, _, _ = select.select([sys.stdin], [], [], .25)
            if readable:
                chunk = os.read(sys.stdin.fileno(), 65536)
                if not chunk:
                    actions.join()
                    break
                pending += chunk
                if len(pending) > 1048576:
                    pending = b''
                    publish(dict(type='error', message='Control message too large'))
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    try:
                        message = json.loads(line)
                        if not isinstance(message, dict):
                            raise ValueError('Invalid control message')
                        actions.put_nowait(message)
                    except (ValueError, queue.Full) as exc:
                        publish(dict(type='error', message=str(exc)))
    finally:
        stopping.set()
        cleanup()

if __name__ == '__main__':
    main()
