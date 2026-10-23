#!/usr/bin/env python3
"""Integrated applications menu/island inside a disposable nested Niri."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'quickshell'))
spec=importlib.util.spec_from_file_location('appearance_preview',ROOT/'scripts/appearance-preview.py')
appearance=importlib.util.module_from_spec(spec);spec.loader.exec_module(appearance)
from applications.model import desktop_entries


def prepare(base):
    config=appearance.prepare(base)
    (base/'applications-catalogue.json').write_text(json.dumps(desktop_entries(),ensure_ascii=False))
    niri=config/'niri/config.kdl';text=niri.read_text()
    text=text.replace('spawn "fuzzel" "--launch-prefix=true"','spawn "qs" "ipc" "-p" "'+str(config/'quickshell')+'" "call" "applications" "menu"')
    niri.write_text(text)
    return config


def client(base,smoke=False,window_modes=False,dashboard_only=False):
    base=Path(base);config=base/'config';children=[]
    log=(base/'applications.log').open('w',buffering=1)
    def rpc(method,*args,target='applications',path=None):
        return subprocess.check_output(['qs','ipc','-p',str(path or config/'quickshell'),'call',target,method,*args],text=True,stderr=subprocess.DEVNULL,timeout=4).strip()
    def status():return json.loads(rpc('status'))
    def wait(predicate,timeout=12):
        value={}
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            try:
                value=status()
                if predicate(value):return value
            except (subprocess.SubprocessError,ValueError):pass
            time.sleep(.1)
        raise RuntimeError('Панель не подтвердила состояние: '+str({k:value.get(k) for k in ('busy','error','panel')}))
    def windows():return json.loads(subprocess.check_output(['niri','msg','-j','windows'],text=True,timeout=4))
    def shot(name):
        time.sleep(.5)
        path=base/(name+'.png')
        subprocess.run(['niri','msg','action','screenshot-screen','--path',str(path)],check=True,stdout=log,stderr=log)
        appearance.wait_for_png(path)
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
    try:
        children.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/preview.py'),'--client',str(base)],stdout=log,stderr=log))
        wait(lambda s:s['entries']>0 and len(s['groups'])>0)
        for title in ('Application preview A','Application preview B'):
            children.append(subprocess.Popen(['alacritty','--config-file',str(config/'alacritty/niri.toml'),'--title',title,'-e','bash','--noprofile','--norc'],stdout=log,stderr=log))
        state=wait(lambda s:any(len(g['windows'])>=3 for g in s['groups']))
        rpc('menu');wait(lambda s:s['panel']=='launcher');shot('applications-launcher')
        (base/'applications-ready').write_text('Menu and isolated desktop ready')
        if window_modes:
            subprocess.run([sys.executable,str(ROOT/'tests/preview_window_modes.py'),str(base)],check=True,stdout=log,stderr=log)
            (base/'applications-result.json').write_bytes((base/'window-modes-result.json').read_bytes())
            return
        if not smoke:
            while children[0].poll() is None:time.sleep(.3)
            return
        fixture=next(w for w in windows() if w['title']=='Application preview A')
        identifier=str(fixture['id'])
        rpc('act','focus',identifier)
        wait(lambda s:any(w['id']==fixture['id'] and w['is_focused'] for g in s['groups'] for w in g['windows']))
        original=next(w for w in windows() if w['id']==fixture['id'])['layout']['window_size']
        rpc('act','fullscreen',identifier)
        wait(lambda s:not s['busy'])
        deadline=time.monotonic()+4
        while next(w for w in windows() if w['id']==fixture['id'])['layout']['window_size']==original:
            if time.monotonic()>deadline:raise RuntimeError('Тестовое окно не перешло в полный экран')
            time.sleep(.1)
        rpc('act','fullscreen',identifier);wait(lambda s:not s['busy'])
        rpc('windows','-');wait(lambda s:s['panel']=='applications');shot('applications-windows')
        rpc('page','main',target='shell')
        shot('quick-settings')
        rpc('page','vpn',target='shell')
        shot('quick-settings-vpn')
        rpc('panel','notifications',target='shell')
        shot('notifications-drawer')
        if dashboard_only:
            children.append(subprocess.Popen([sys.executable,str(base/'mpris_mock.py'),str(base/'dashboard-mpris.jsonl')],stdout=log,stderr=log))
            deadline=time.monotonic()+6
            while not json.loads(rpc('status',target='shell'))['title']:
                if time.monotonic()>deadline:raise RuntimeError('MPRIS player not discovered')
                time.sleep(.1)
            rpc('media','toggle',target='shell')
            deadline=time.monotonic()+4
            while json.loads(rpc('status',target='shell'))['playing']:
                if time.monotonic()>deadline:raise RuntimeError('MPRIS pause not confirmed')
                time.sleep(.1)
            rpc('media','toggle',target='shell')
        rpc('page','overview',target='dashboard')
        deadline=time.monotonic()+6
        while True:
            dashboard=json.loads(rpc('status',target='dashboard'))
            if dashboard['metrics'].get('cpu') is not None:break
            if time.monotonic()>deadline:raise RuntimeError('Дашборд не получил CPU sample')
            time.sleep(.1)
        shot('dashboard-overview')
        rpc('page','performance',target='dashboard');shot('dashboard-performance')

        if dashboard_only:
            rpc('panel','',target='shell')
            time.sleep(.3)
            stopped=json.loads(rpc('status',target='dashboard'))
            if stopped['active'] or stopped['samples']:raise RuntimeError('Сбор показателей не остановлен')
            (base/'applications-result.json').write_text(json.dumps(dict(passed=True,dashboard=True,metrics=True,lifecycle=True)))
            return

        rpc('panel','',target='shell')
        before=len(windows())
        rpc('act','launch','Alacritty.desktop')
        wait(lambda s:not s['busy'] and sum(len(g['windows']) for g in s['groups'])==before+1)
        rpc('act','close',identifier)
        wait(lambda s:not any(w['id']==fixture['id'] for g in s['groups'] for w in g['windows']))
        rpc('act','launch','firefox.desktop')
        wait(lambda s:not s['busy'] and bool(s['error']))
        shot('applications-error-message')
        rpc('act','settings','-');wait(lambda s:not s['busy'] and s['error']=='')
        deadline=time.monotonic()+12
        while True:
            try:
                settings=json.loads(rpc('status',target='appearance',path=config/'quickshell/appearance-ui'))
                if settings['themes']==22 and settings['wallpapers']==11:break
            except (subprocess.SubprocessError,ValueError):pass
            if time.monotonic()>deadline:raise RuntimeError('Меню не открыло окно оформления')
            time.sleep(.1)
        shot('applications-settings')
        (base/'applications-result.json').write_text(json.dumps(dict(passed=True,focus=True,fullscreen=True,close=True,safe_launch=True,blocked_external_launch=True,appearance=True,entries=state['entries'],groups=len(state['groups'])),indent=2))
    except Exception as exc:
        (base/'applications-error').write_text(str(exc)+'\n'+traceback.format_exc())
        raise
    finally:
        for child in children:
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=4)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--dashboard-only',action='store_true')
    parser.add_argument('--window-modes',action='store_true',help='Check floating/tiling round trip in a disposable session')
    parser.add_argument('--client',help=argparse.SUPPRESS);parser.add_argument('--client-smoke',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.client:return client(args.client,args.client_smoke,args.window_modes,args.dashboard_only)
    if args.window_modes or args.dashboard_only:args.smoke=True
    base=Path(tempfile.mkdtemp(prefix='niri-applications-'));print('Applications preview:',base,flush=True)
    config=prepare(base)
    subprocess.run(['niri','validate','-c',str(config/'niri/config.kdl')],check=True)
    if args.check:print('PASS: private files prepared');return
    runtime=os.environ.get('XDG_RUNTIME_DIR');display=os.environ.get('WAYLAND_DISPLAY')
    if not runtime or not display:raise RuntimeError('Нужна Wayland-сессия')
    env={k:os.environ[k] for k in ('PATH','LANG','LC_ALL','USER','LOGNAME') if k in os.environ}
    env.update(HOME=str(base/'home'),XDG_CONFIG_HOME=str(config),XDG_CACHE_HOME=str(base/'cache'),XDG_DATA_HOME=str(base/'data'),
        XDG_STATE_HOME=str(base/'state'),XDG_RUNTIME_DIR=str(base/'runtime'),WAYLAND_DISPLAY=str(Path(runtime)/display),
        WINIT_UNIX_BACKEND='wayland',GDK_BACKEND='wayland',QT_QPA_PLATFORM='wayland',GTK_USE_PORTAL='0',NO_AT_BRIDGE='1',
        GIO_USE_VFS='local',NIRI_SHELL_PREVIEW='1',NIRI_PREVIEW_SMOKE='0',NIRI_SHELL_LEGACY='0',PYTHONDONTWRITEBYTECODE='1')
    command=['dbus-run-session','--config-file',str(base/'dbus.conf'),'--','niri','-c',str(config/'niri/config.kdl'),'--',sys.executable,str(Path(__file__).resolve()),'--client',str(base)]
    if args.smoke:command.append('--client-smoke')
    if args.window_modes:command.append('--window-modes')
    if args.dashboard_only:command.append('--dashboard-only')
    with (base/'preview.log').open('w') as log:
        process=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            if args.smoke:
                deadline=time.monotonic()+55
                while not (base/'applications-result.json').exists() and not (base/'applications-error').exists() and process.poll() is None:
                    if time.monotonic()>deadline:raise RuntimeError('Предпросмотр не завершил проверку за 55 секунд')
                    time.sleep(.2)
            else:process.wait()
        except KeyboardInterrupt:pass
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    if (base/'applications-error').exists():raise RuntimeError((base/'applications-error').read_text())
    if args.smoke:
        if not (base/'applications-result.json').exists():raise RuntimeError('Нет результата GUI, см. '+str(base))
        for file in ('components.log','applications.log'):
            if re.search(r'TypeError|ReferenceError|Unable to assign|Binding loop|Failed to load configuration',(base/file).read_text()):raise RuntimeError('Ошибки GUI, см. '+str(base/file))
        print('PASS: '+('dashboard GUI, metrics and collection lifecycle' if args.dashboard_only else 'applications GUI and real window actions')+';',base)
    else:print('Preview stopped:',base)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:sys.exit(str(exc))
