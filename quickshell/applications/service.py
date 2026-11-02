"""Native commands are ID-scoped and currently enabled only in private preview."""
import json
from pathlib import Path
import subprocess
import sys
from preview_scope import require_session, session_enabled
from .model import groups
from .window_modes import WindowModes
from .usage import Usage


class ApplicationService:
    def __init__(self,root,state_dir,entries,preview=False,runner=subprocess.run):
        self.root=Path(root).resolve();self.state_dir=Path(state_dir).resolve()
        self.entries=entries;self.preview=preview;self.runner=runner;self.children=[]
        self.modes=WindowModes(self.root,self.state_dir,preview,self.command)
        self.usage=Usage(self.state_dir/'application-usage.json')

    def command(self,args):
        result=self.runner(args,capture_output=True,text=True,check=True,timeout=4)
        if result.returncode:raise RuntimeError(result.stderr or 'Команда Niri не выполнена')
        return result.stdout

    def snapshot(self):
        windows=json.loads(self.command(['niri','msg','-j','windows']))
        if self.modes.reconcile(windows):windows=json.loads(self.command(['niri','msg','-j','windows']))
        workspaces=json.loads(self.command(['niri','msg','-j','workspaces']))
        app_groups=groups(self.entries,windows,workspaces)
        focused=next((g for g in app_groups if g['active']),None)
        if focused is not None and session_enabled(self.root,self.state_dir,self.preview):
            try:self.usage.observe(focused['desktop_id'])
            except (OSError,ValueError):pass # A failed history write must not break the application menu.
        return dict(groups=app_groups,workspaces=workspaces,preview=self.preview,window_modes=self.modes.status(),usage=self.usage.counts.copy())

    def action(self,action,value=None):
        require_session(self.root,self.state_dir,self.preview)
        if action=='workspace-mode':
            self.modes.toggle(value);return
        if action=='launch':
            if value not in {e['id'] for e in self.entries}:raise ValueError('Приложение больше не установлено')
            if not self.preview:
                if value=='Alacritty.desktop':
                    subprocess.Popen(['alacritty','--config-file',str(self.root/'alacritty/niri.toml')],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                else:
                    import gi
                    gi.require_version('GioUnix','2.0')
                    from gi.repository import GioUnix, GLib
                    app=GioUnix.DesktopAppInfo.new(value)
                    try:
                        # Keep child diagnostics out of the bridge's JSON-lines stdout.
                        flags=GLib.SpawnFlags.SEARCH_PATH|GLib.SpawnFlags.STDOUT_TO_DEV_NULL|GLib.SpawnFlags.STDERR_TO_DEV_NULL
                        if app is None or not app.launch_uris_as_manager([],None,flags,None,None,None,None):
                            raise ValueError('Не удалось запустить установленное приложение')
                    except Exception as exc:raise RuntimeError('Не удалось запустить приложение: '+str(exc)) from exc
                return
            if value!='Alacritty.desktop':
                raise ValueError('В предпросмотре запускается только тестовый терминал. '+
                    'Firefox, ChatGPT и Happ будут доступны после применения окружения.')
            profile=self.root/'alacritty/niri.toml'
            if not profile.is_file():raise ValueError('Нет отдельного профиля тестового терминала')
            self.children.append(subprocess.Popen(['alacritty','--config-file',str(profile),'-e','bash','--noprofile','--norc'],stdout=sys.stderr,stderr=sys.stderr))
            return
        if action=='settings':
            ui=self.root/'quickshell/appearance-ui'
            try:self.command(['qs','ipc','-p',str(ui),'call','--','appearance','show'])
            except (RuntimeError,subprocess.SubprocessError):
                self.children.append(subprocess.Popen(['qs','-p',str(ui)],stdout=sys.stderr,stderr=sys.stderr))
            return
        commands=dict(focus='focus-window',close='close-window',fullscreen='fullscreen-window',maximize='maximize-window-to-edges')
        if action not in commands:raise ValueError('Это действие не поддерживается Niri')
        if type(value) is not int or not 0<=value<2**64:raise ValueError('Некорректный идентификатор окна')
        windows=json.loads(self.command(['niri','msg','-j','windows']))
        window=next((w for w in windows if w['id']==value),None)
        if window is None:raise ValueError('Окно уже закрыто')
        if action=='maximize' and not window.get('is_floating'):raise ValueError('Разворачивание до краёв доступно для плавающего окна')
        self.command(['niri','msg','action',commands[action],'--id',str(value)])

    def close(self):
        for child in self.children:
            if child.poll() is None:child.terminate()
        for child in self.children:
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:child.kill();child.wait()
