#!/usr/bin/env python3
"""Open appearance settings in a disposable nested Niri session."""
import argparse
import hashlib
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
import traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import preview as desktop_preview

def wait_for_png(path,timeout=4):
    from PIL import Image
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:
            with Image.open(path) as image:image.verify()
            return path
        except (OSError,SyntaxError):time.sleep(.05)
    raise RuntimeError('Снимок не успел сохраниться: '+str(path))

def prepare(base):
    config=desktop_preview.prepare(base)
    shutil.copytree(ROOT/'gtklock',config/'gtklock',symlinks=False,ignore=shutil.ignore_patterns('*.so','__pycache__'))
    state=base/'state/niri-shell'
    (base/'.appearance-preview.json').write_text(json.dumps(dict(root=str(config),state=str(state),runtime=str(base/'runtime'))))
    source=(config/'alacritty/alacritty.toml').read_text()
    imports=[str(config/'assets/themes/current/alacritty.toml'),str(config/'alacritty/opacity.toml')]
    source=re.sub(r'\[general\]\s*\nimport\s*=\s*\[[^\]]*\]','[general]\nimport = '+json.dumps(imports),source,count=1)
    source=re.sub(r'(?ms)^\[colors(?:\.[^\]]*)?\].*?(?=^\[|\Z)','',source)
    (config/'alacritty/niri.toml').write_text(source)
    niri=config/'niri/config.kdl'
    text=niri.read_text().replace('binds {','binds {\n    Mod+Shift+O { spawn "qs" "ipc" "-p" "'+str(config/'quickshell/appearance-ui')+'" "call" "--" "appearance" "show"; }',1)
    text=text.replace('spawn "alacritty" "-e"','spawn "alacritty" "--config-file" "'+str(config/'alacritty/niri.toml')+'" "-e"')
    text+='\noutput \"winit\" { scale 1.6; }\nwindow-rule { match title=\"^Настройки Niri\"; open-floating true; }\n'
    niri.write_text(text)
    return config

def client(base):
    base=Path(base);config=base/'config';processes=[]
    log=(base/'appearance.log').open('w',buffering=1)
    def rpc(method,*args):
        return subprocess.check_output(['qs','ipc','-p',str(config/'quickshell/appearance-ui'),'call','--','appearance',method,*args],text=True,stderr=subprocess.DEVNULL,timeout=3).strip()
    def state():
        return json.loads(rpc('status'))
    def wait(predicate,timeout=10):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            try:
                value=state()
                if not value['busy'] and value['error']:raise RuntimeError(value['error'])
                if predicate(value):return value
            except (subprocess.SubprocessError,json.JSONDecodeError):pass
            time.sleep(.1)
        raise RuntimeError('Настройки не подтвердили готовность')
    def stop(*_):
        for p in processes:
            if p.poll() is None:p.terminate()
        for p in processes:
            try:p.wait(timeout=4)
            except subprocess.TimeoutExpired:p.kill();p.wait()
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
    try:
        processes.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/preview.py'),'--client',str(base)],stdout=log,stderr=log))
        deadline=time.monotonic()+14
        while not (base/'ready').exists():
            if (base/'client-error').exists():raise RuntimeError((base/'client-error').read_text())
            if time.monotonic()>deadline:raise RuntimeError('Рабочий стол предпросмотра не запустился')
            time.sleep(.1)
        ui=['qs','-p',str(config/'quickshell/appearance-ui')]
        # The existing preview's first terminal uses the isolated HOME. Open one
        # with the dedicated profile too, so its hot-reload path can be inspected.
        processes.append(subprocess.Popen(['alacritty','--config-file',str(config/'alacritty/niri.toml'),'-e','bash','--noprofile','--norc'],stdout=log,stderr=log))
        processes.append(subprocess.Popen(ui,stdout=log,stderr=log))
        wait(lambda s:s.get('themes')==22 and s.get('wallpapers')==11)
        rpc('show')
        if os.environ.get('NIRI_APPEARANCE_SMOKE')=='1':
            before=state()['selection']
            outputs=json.loads(subprocess.check_output(['niri','msg','-j','outputs'],text=True))
            output=next(iter(outputs))
            logical=outputs[output]['logical']
            settings_window=None
            for _ in range(30):
                windows=json.loads(subprocess.check_output(['niri','msg','-j','windows'],text=True,timeout=3))
                settings_window=next((w for w in windows if w.get('title')=='Настройки Niri · Оформление'),None)
                if settings_window is not None:break
                time.sleep(.1)
            assert settings_window is not None, 'Settings did not map'
            assert settings_window['is_floating'], 'Settings preview should use its own floating rule'
            rpc('choosePalette','hyprstack:catppuccin','light','blue')
            light=wait(lambda s:not s['busy'] and s['selection'].get('mode')=='light')
            assert light['selection']['wallpaper_id']==before['wallpaper_id']
            time.sleep(.6)
            subprocess.run(['niri','msg','action','screenshot-screen','--path',str(base/'appearance-colors.png')],check=True,stdout=log,stderr=log)
            wait_for_png(base/'appearance-colors.png')
            catalogue=json.loads((config/'assets/appearance/catalog.json').read_text())
            gif=next(w for w in catalogue['wallpapers'] if w['frames']>1)
            rpc('page','wallpapers')
            rpc('chooseWallpaper',gif['id'])
            selected=wait(lambda s:not s['busy'] and s['selection'].get('wallpaper_id')==gif['id'])
            assert (selected['selection']['mode'],selected['selection']['accent_id'])==('light','blue')
            time.sleep(.8)
            subprocess.run(['niri','msg','action','screenshot-screen','--path',str(base/'appearance-wallpapers.png')],check=True,stdout=log,stderr=log)
            wait_for_png(base/'appearance-wallpapers.png')
            # Restart settings only; do not kill or restart the desktop shell.
            settings=processes[-1];settings.terminate();settings.wait(timeout=4)
            processes[-1]=subprocess.Popen(ui,stdout=log,stderr=log)
            restarted=wait(lambda s:not s['busy'] and s['selection']==selected['selection'])
            rpc('show');rpc('page','wallpapers');time.sleep(.6)
            subprocess.run(['niri','msg','action','screenshot-screen','--path',str(base/'appearance-restored.png')],check=True,stdout=log,stderr=log)
            wait_for_png(base/'appearance-restored.png')
            (base/'appearance-result.json').write_text(json.dumps(dict(passed=True,before=before,after=restarted['selection'],themes=22,wallpapers=11,scale=1.6,logical_output=logical),indent=2))
            return
        (base/'appearance-ready').write_text('Settings and isolated desktop ready')
        while processes[-1].poll() is None and processes[0].poll() is None:time.sleep(.3)
    except Exception as exc:
        (base/'appearance-error').write_text(type(exc).__name__+': '+str(exc)+'\n'+traceback.format_exc())
        raise
    finally:stop();log.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--client',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.client:return client(args.client)
    base=Path(tempfile.mkdtemp(prefix='niri-appearance-'))
    print('Appearance preview:',base,flush=True)
    config=prepare(base)
    subprocess.run(['niri','validate','-c',str(config/'niri/config.kdl')],check=True)
    if args.check:
        print('PASS: disposable settings files prepared; no windows or live changes')
        return
    for command in ('niri','qs','alacritty','awww','awww-daemon','dbus-run-session'):
        if not shutil.which(command):raise RuntimeError('Missing dependency: '+command)
    runtime=os.environ.get('XDG_RUNTIME_DIR');display=os.environ.get('WAYLAND_DISPLAY')
    if not runtime or not display:raise RuntimeError('Запустите предпросмотр из Wayland-сессии')
    env={k:os.environ[k] for k in ('PATH','LANG','LC_ALL','USER','LOGNAME') if k in os.environ}
    env.update(HOME=str(base/'home'),XDG_CONFIG_HOME=str(config),XDG_CACHE_HOME=str(base/'cache'),XDG_DATA_HOME=str(base/'data'),
        XDG_STATE_HOME=str(base/'state'),XDG_RUNTIME_DIR=str(base/'runtime'),WAYLAND_DISPLAY=str(Path(runtime)/display),
        WINIT_UNIX_BACKEND='wayland',GDK_BACKEND='wayland',QT_QPA_PLATFORM='wayland',GTK_USE_PORTAL='0',NO_AT_BRIDGE='1',
        GIO_USE_VFS='local',NIRI_SHELL_PREVIEW='1',NIRI_PREVIEW_SMOKE='0',NIRI_SHELL_LEGACY='0',
        NIRI_APPEARANCE_SMOKE='1' if args.smoke else '0',PYTHONDONTWRITEBYTECODE='1')
    command=['dbus-run-session','--config-file',str(base/'dbus.conf'),'--','niri','-c',str(config/'niri/config.kdl'),'--',sys.executable,str(Path(__file__).resolve()),'--client',str(base)]
    with (base/'preview.log').open('w') as log:
        process=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            if args.smoke:
                deadline=time.monotonic()+45
                while not (base/'appearance-result.json').exists() and not (base/'appearance-error').exists() and process.poll() is None:
                    if time.monotonic()>deadline:raise RuntimeError('Предпросмотр не завершил проверки за 45 секунд')
                    time.sleep(.2)
            else:process.wait()
        except KeyboardInterrupt:pass
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=6)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    if (base/'appearance-error').exists():raise RuntimeError((base/'appearance-error').read_text())
    if args.smoke:
        if not (base/'appearance-result.json').exists():raise RuntimeError('Нет подтверждения GUI-проверки; журнал '+str(base/'appearance.log'))
        text=(base/'appearance.log').read_text()
        if re.search(r'TypeError|ReferenceError|Unable to assign|Binding loop|Failed to load configuration',text):
            raise RuntimeError('Ошибки GUI; журнал '+str(base/'appearance.log'))
        print('PASS: GUI palette/wallpaper selection and restart persistence; screenshots:',base)
    else:print('Preview stopped:',base)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:sys.exit(str(exc))
