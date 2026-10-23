#!/usr/bin/env python3
"""Run a disposable nested Niri desktop; never install its configuration."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from niri_config import flatten


def jsonc(text):
    # Preserve quoted strings while removing comments.
    return json.loads(re.sub(r'("(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/)',
                             lambda m: m[0] if m[0].startswith('"') else '', text))


def prepare(base, legacy=False):
    config = base / 'config'
    config.mkdir()
    shutil.copy2(ROOT/'tests/mpris_mock.py', base/'mpris_mock.py')
    for name in ('niri', 'eww', 'waybar', 'alacritty', 'assets', 'quickshell', 'fuzzel'):
        shutil.copytree(ROOT / name, config / name, symlinks=False, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Test-only IPC injection: never included in deployed shell.qml.
    shell_file = config/'quickshell/shell.qml'
    shell_text = shell_file.read_text().replace('        function status(): string',
        '        function previewOsd(kind: string): void { root.osdKind = kind }\n        function status(): string')
    shell_file.write_text(shell_text)
    # Copied theme symlinks are materialized; there is no path back to the checkout.
    for path in config.rglob('*'):
        if path.is_file():
            try:
                text = path.read_text()
            except UnicodeError:
                continue
            path.write_text(text.replace(str(ROOT), str(config)))
    niri = config / 'niri/config.kdl'
    text = flatten(niri)
    text = re.sub(r'^spawn(?:-sh)?-at-startup[^\n]*\n', '', text, flags=re.M)
    # Preserve tiling/navigation/appearance; external commands are replaced by a
    # deliberately small set below. Fail closed if a future bind is multiline.
    lines = []
    for line in text.splitlines():
        if not line.lstrip().startswith('//') and re.search(r'\bspawn(?:-sh)?\s', line):
            if '{' not in line or '}' not in line:
                raise ValueError('Multiline spawn bind: review preview filtering before use')
            continue
        lines.append(line)
    text = '\n'.join(lines)
    text = text.replace('hotkey-overlay {', 'hotkey-overlay {\n    skip-at-startup', 1)
    text = text.replace('binds {', '''binds {
    Mod+T { spawn "alacritty" "-e" "bash" "--noprofile" "--norc"; }
    Mod+E { spawn "qs" "ipc" "call" "shell" "panel" "right"; }
    Mod+Shift+M { spawn "qs" "ipc" "call" "shell" "panel" "center"; }
    Mod+Space { spawn "fuzzel" "--launch-prefix=true"; }
''', 1)
    # Mod defaults to Alt in a nested compositor; avoid consuming host Super keys.
    text = text.replace('input {', 'input {\n    mod-key-nested "Alt";', 1)
    text += '\nxwayland-satellite { off; }\n'
    text += '\nenvironment { DISPLAY null; GTK_USE_PORTAL "0"; }\n'
    if legacy:
        text = text.replace('spawn \"qs\" \"ipc\" \"call\" \"shell\" \"panel\" \"right\"', 'spawn \"eww\" \"open\" \"control_center\"')
        text = text.replace('spawn \"qs\" \"ipc\" \"call\" \"shell\" \"panel\" \"center\"', 'spawn \"eww\" \"open\" \"media_popup\"')
    niri.write_text(text)
    wallpapers = sorted(p for p in (config/'assets/themes/current').iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    if not wallpapers:
        raise RuntimeError('Selected theme has no desktop wallpaper')
    (base/'wallpaper-path').write_text(str(wallpapers[0]))
    eww = config / 'eww/eww.yuck'
    text = eww.read_text()
    defaults = dict(volume='45', brightness='70', track_title='"Тестовый трек"',
                    track_artist='"Предпросмотр"', play_status='"Paused"', cover_art='""',
                    song_pos='30', song_length='180', song_pos_fmt='"0:30"', song_len_fmt='"3:00"')
    # Existing polls are single-line declarations; no background system queries.
    text = re.sub(r'^\(defpoll\s+(\w+)[^\n]*$',
                  lambda m: f'(defvar {m[1]} {defaults[m[1]]})', text, flags=re.M)
    allowed = ('eww ',)
    text = re.sub(r':(onclick|onchange)\s+"((?:\\.|[^"\\])*)"',
                  lambda m: m[0] if m[2].startswith(allowed) else f':{m[1]} "true"', text)
    text = text.replace('(defvar open_cc false)', '(defvar open_cc true)').replace('(defvar media_open false)', '(defvar media_open true)')
    # No empty artwork warning in the mock player.
    text = text.replace(':path cover_art', ':path "' + str(wallpapers[0]) + '"')
    eww.write_text(text)
    bar = jsonc((config/'waybar/config.jsonc').read_text())
    bar['modules-center'] = ['clock', 'custom/preview-media']
    bar['modules-right'] = ['niri/language', 'custom/preview-status', 'custom/quicksettings']
    bar['custom/launcher'] = {'format': 'ТЕСТ', 'tooltip': True, 'tooltip-format': 'Alt+T — терминал · Alt+Shift+E — выход'}
    bar['custom/preview-media'] = {'format': '♫ Предпросмотр', 'on-click': str(config/'eww/scripts/toggle-win.sh')+' media_popup'}
    bar['custom/preview-status'] = {'format': '󰕾 45%  ▰ 82%', 'tooltip-format': 'Демонстрационные значения'}
    active = {name for key in ('modules-left', 'modules-center', 'modules-right') for name in bar[key]}
    for key in list(bar):
        if isinstance(bar[key], dict) and key not in active:
            del bar[key]
    for key in active:
        if isinstance(bar.get(key), dict):
            for action in list(bar[key]):
                if action.startswith('on-') and key not in ('custom/quicksettings', 'custom/preview-media'):
                    del bar[key][action]
    (config/'waybar/config.jsonc').write_text(json.dumps(bar, ensure_ascii=False, indent=2))
    # Use an isolated non-login terminal, without the user's shell startup files.
    for name in ('runtime', 'cache', 'data', 'state', 'home'):
        (base/name).mkdir(mode=0o700)
    (base/'dbus.conf').write_text('<busconfig><type>session</type>'
        f'<listen>unix:tmpdir={base / "runtime"}</listen>'
        '<policy context="default"><allow send_destination="*"/>'
        '<allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    return config


def client(base):
    base = Path(base)
    log = (base/'components.log').open('w', buffering=1)
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    children = []
    def stop(*_):
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    (base/'client.pid').write_text(str(os.getpid()))
    try:
        if os.environ.get('NIRI_PREVIEW_SMOKE') == '1' and os.environ.get('NIRI_SHELL_LEGACY') != '1':
            children.append(subprocess.Popen([sys.executable, str(base/'mpris_mock.py'), str(base/'mpris-actions.jsonl')]))
        smoke_widgets = None
        if os.environ.get('NIRI_PREVIEW_SMOKE') == '1' and os.environ.get('NIRI_SHELL_LEGACY') != '1':
            outputs = json.loads(subprocess.check_output(['niri', 'msg', '-j', 'outputs'], text=True))
            output = next(iter(outputs))
            layout = dict(clock=dict(x=.08, y=.22, width=400, height=240, visible=True),
                          media=dict(x=.45, y=.22, width=260, height=300, visible=True),
                          weather=dict(x=.65, y=.60, width=320, height=180, visible=True))
            smoke_widgets = {'_version': 2, output: {'workspaces': {'index:1': layout, 'index:2': layout}}}
            folder = base/'state/niri-shell'
            folder.mkdir(parents=True, exist_ok=True)
            (folder/'widgets.json').write_text(json.dumps(smoke_widgets))
        shell_commands = ([['eww', '--no-daemonize', 'daemon'], ['waybar']] if os.environ.get('NIRI_SHELL_LEGACY') == '1' else [['qs', '-p', str(base/'config/quickshell')]])
        for command in shell_commands + [['awww-daemon'], ['alacritty', '-e', 'bash', '--noprofile', '--norc']]:
            children.append(subprocess.Popen(command))
        for _ in range(40):
            if subprocess.run(['awww', 'query'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Preview wallpaper daemon did not become ready')
        for _ in range(40):
            query = subprocess.run(['awww', 'query'], capture_output=True, text=True, timeout=2)
            if query.returncode == 0 and 'currently displaying:' in query.stdout:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Wallpaper daemon has no configured output')
        subprocess.run(['awww', 'img', '--transition-type', 'none', (base/'wallpaper-path').read_text()], check=True)
        (base/'wallpaper-status').write_text(subprocess.run(['awww', 'query'], capture_output=True, text=True, check=True).stdout)
        if os.environ.get('NIRI_SHELL_LEGACY') == '1':
            for _ in range(30):
                if subprocess.run(['eww', 'ping'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('Eww did not become ready')
        else:
            for _ in range(50):
                if subprocess.run(['qs', 'ipc', 'call', 'shell', 'panel', ''], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('Quickshell did not become ready; see components.log')
            if os.environ.get('NIRI_PREVIEW_SMOKE') == '1':
                for _ in range(30):
                    status = json.loads(subprocess.check_output(['qs', 'ipc', 'call', 'shell', 'status'], text=True))
                    if status['title'] == 'Тестовый трек': break
                    time.sleep(.1)
                else:
                    raise RuntimeError('MPRIS player was not discovered')
                subprocess.run(['qs', 'ipc', 'call', 'shell', 'media', 'toggle'], check=True)
                subprocess.run(['qs', 'ipc', 'call', 'shell', 'media', 'next'], check=True)
                # Restart only the disposable shell and check exact saved geometry.
                shell_process = next(child for child in children if isinstance(child.args, list) and child.args[0] == 'qs')
                shell_process.terminate(); shell_process.wait(timeout=5); children.remove(shell_process)
                children.append(subprocess.Popen(['qs', '-p', str(base/'config/quickshell')]))
                for _ in range(50):
                    ready = subprocess.run(['qs', 'ipc', 'call', 'shell', 'status'], capture_output=True, text=True)
                    if ready.returncode == 0 and json.loads(ready.stdout).get('widgets') == smoke_widgets:
                        break
                    time.sleep(.1)
                else:
                    raise RuntimeError('Widget positions were not restored after restarting Quickshell')
                # Change only the nested output scale, then restore it.
                nested_output = next(iter(json.loads(subprocess.check_output(['niri', 'msg', '-j', 'outputs'], text=True))))
                for scale in ('1.25', '1'):
                    subprocess.run(['niri', 'msg', 'output', nested_output, 'scale', scale], check=True)
                    time.sleep(.3)
                    restored = json.loads(subprocess.check_output(['qs', 'ipc', 'call', 'shell', 'status'], text=True))
                    if restored['widgets'] != smoke_widgets:
                        raise RuntimeError('Scale change overwrote saved widget geometry')
                for kind in ('brightness', '', 'volume', '', 'mic_volume', 'brightness'):
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'previewOsd', kind], check=True)
                    time.sleep(.15)
                subprocess.run(['niri', 'msg', 'action', 'screenshot-screen', '--path', str(base/'osd.png')], check=True)
                subprocess.run(['qs', 'ipc', 'call', 'shell', 'previewOsd', ''], check=True)
                (base/'widget-checks.json').write_text(json.dumps(dict(restart=True, scale=True, widgets=smoke_widgets)))
                for page_name in ('wifi', 'bluetooth', 'audio', 'vpn', 'desktop', 'main'):
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'page', page_name], check=True)
                    time.sleep(.25)
                    subprocess.run(['niri', 'msg', 'action', 'screenshot-screen', '--path', str(base/(page_name+'-page.png'))], check=True)
                for panel in ('center', 'right'):
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'panel', panel], check=True)
                    time.sleep(.6)
                    subprocess.run(['niri', 'msg', 'action', 'screenshot-screen', '--path', str(base/(panel+'.png'))], check=True)
                # Verify real backend persistence and both editor views in the isolated profile.
                for panel, values in (('center', ['weather', 'media', 'calendar', 'audio']), ('right', []), ('right', ['calendar', 'media', 'connectivity', 'vpn', 'audio', 'brightness', 'power', 'desktop'])):
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'modules', panel, ','.join(values) or '-'], check=True)
                    for _ in range(30):
                        status = json.loads(subprocess.check_output(['qs', 'ipc', 'call', 'shell', 'status'], text=True))
                        if status.get('panels', {}).get(panel) == values: break
                        time.sleep(.1)
                    else: raise RuntimeError('Panel layout did not update')
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'panel', panel], check=True)
                    time.sleep(.4)
                    subprocess.run(['niri', 'msg', 'action', 'screenshot-screen', '--path', str(base/(panel+'-custom.png'))], check=True)
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'customize', panel], check=True)
                    time.sleep(.4)
                    subprocess.run(['niri', 'msg', 'action', 'screenshot-screen', '--path', str(base/(panel+'-picker.png'))], check=True)
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'customize', ''], check=True)
                for panel, values in (('center', ['calendar', 'media']), ('right', ['connectivity', 'vpn', 'audio', 'brightness', 'power', 'desktop'])):
                    subprocess.run(['qs', 'ipc', 'call', 'shell', 'modules', panel, ','.join(values) or '-'], check=True)
                subprocess.run(['qs', 'ipc', 'call', 'shell', 'panel', ''], check=True)
                # Exercise Fuzzel config without launching real applications.
                menu = subprocess.Popen(['fuzzel', '--launch-prefix=true'])
                children.append(menu)
                time.sleep(.5)
                if menu.poll() is not None:
                    raise RuntimeError('Fuzzel exited before preview capture')
                subprocess.run(['niri', 'msg', 'action', 'screenshot-screen', '--path', str(base/'fuzzel.png')], check=True)
                menu.terminate(); menu.wait(); children.remove(menu)
        time.sleep(1)
        subprocess.run(['niri', 'msg', 'action', 'focus-workspace', '2'], check=True)
        if os.environ.get('NIRI_PREVIEW_SMOKE') == '1':
            subprocess.run(['niri', 'msg', 'action', 'focus-workspace', '2'], check=True)
            time.sleep(.5)
            subprocess.run(['niri', 'msg', 'action', 'screenshot-screen', '--path', str(base/'desktop.png')], check=True)
        if any(child.poll() is not None for child in children):
            raise RuntimeError('A preview component exited during startup')
        (base/'ready').write_text('Preview shell, awww and Alacritty started')
        socket = Path(os.environ['NIRI_SOCKET'])
        while socket.exists():
            time.sleep(.3)
    except Exception as exc:
        (base/'client-error').write_text(str(exc))
    finally:
        stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy', action='store_true', help='Preview the previous Waybar/Eww shell')
    parser.add_argument('--check', action='store_true', help='Generate and validate without opening windows')
    parser.add_argument('--smoke', action='store_true', help='Close the test window automatically after 18 seconds')
    parser.add_argument('--client', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.client:
        return client(args.client)
    for binary in ('niri', 'dbus-run-session', 'eww', 'waybar', 'awww', 'awww-daemon', 'alacritty', 'qs', 'fuzzel'):
        if not shutil.which(binary):
            raise RuntimeError(f'Missing dependency: {binary}')
    parent_display = os.environ.get('WAYLAND_DISPLAY')
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not args.check and (not parent_display or not runtime):
        raise RuntimeError('Run this command from a terminal in your current Wayland desktop.')
    base = Path(tempfile.mkdtemp(prefix='niri-preview-'))
    print(f'Preview files and logs: {base}', flush=True)
    config = prepare(base, args.legacy)
    subprocess.run(['niri', 'validate', '-c', str(config/'niri/config.kdl')], check=True)
    if args.check:
        print('Configuration valid. No windows opened; no live configuration changed.')
        return
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'USER', 'LOGNAME') if key in os.environ}
    env.update(HOME=str(base/'home'), XDG_CONFIG_HOME=str(config), XDG_CACHE_HOME=str(base/'cache'),
               XDG_DATA_HOME=str(base/'data'), XDG_STATE_HOME=str(base/'state'), XDG_RUNTIME_DIR=str(base/'runtime'),
               WAYLAND_DISPLAY=str(Path(runtime)/parent_display), WINIT_UNIX_BACKEND='wayland',
               GDK_BACKEND='wayland', QT_QPA_PLATFORM='wayland', GTK_USE_PORTAL='0',
               NO_AT_BRIDGE='1', GIO_USE_VFS='local', NIRI_SHELL_PREVIEW='1', NIRI_SHELL_LEGACY='1' if args.legacy else '0', NIRI_PREVIEW_SMOKE='1' if args.smoke else '0')
    command = ['dbus-run-session', '--config-file', str(base/'dbus.conf'), '--', 'niri', '-c', str(config/'niri/config.kdl'), '--',
               sys.executable, str(Path(__file__).resolve()), '--client', str(base)]
    print('Alt+T: terminal. Alt+Shift+E: exit preview. Ctrl+C in this terminal also stops it.', flush=True)
    with (base/'preview.log').open('w') as log:
        proc = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            proc.wait(timeout=18 if args.smoke else None)
        except (KeyboardInterrupt, subprocess.TimeoutExpired):
            pass
        finally:
            pid = base/'client.pid'
            if pid.exists():
                try:
                    os.kill(int(pid.read_text()), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
    print(f'Preview stopped. Log: {base}/preview.log')
    if (base/'client-error').exists():
        raise RuntimeError((base/'client-error').read_text())
    if args.smoke and not (base/'ready').exists():
        raise RuntimeError('Preview did not become ready; see '+str(base/'preview.log'))
    if args.smoke and not args.legacy:
        actions = [json.loads(line)['method'] for line in (base/'mpris-actions.jsonl').read_text().splitlines()]
        if not any(action in actions for action in ('Pause', 'PlayPause')) or 'Next' not in actions:
            raise RuntimeError('MPRIS integration commands were not received')
        component_log = (base/'components.log').read_text()
        if re.search(r'TypeError|ReferenceError|not a valid option|Failed to load configuration|Unable to assign|Binding loop detected', component_log):
            raise RuntimeError('Component errors found; see components.log')
    if args.smoke and not (base/'ready').exists():
        raise RuntimeError('Preview did not become ready; see log')
    if not args.smoke and proc.returncode not in (0, -signal.SIGTERM):
        raise RuntimeError(f'Preview exited with code {proc.returncode}; see log.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
