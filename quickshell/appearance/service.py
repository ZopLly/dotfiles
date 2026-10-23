"""Appearance activation is deliberately limited to a verified disposable preview."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
import tempfile
import time
import uuid
from contextlib import contextmanager
from preview_scope import require_session, session_enabled
from .catalog import Catalogue
from .palette import resolve_palette
from .render import render_theme
from .store import Store, initial_selection

class AppearanceService:
    def __init__(self,root,state_dir,preview=False,runner=subprocess.run):
        self.root=Path(root).resolve()
        self.state_dir=Path(state_dir).resolve()
        self.preview=preview
        self.runner=runner
        self.catalogue=Catalogue(self.root)
        self.store=Store(self.state_dir/'appearance.json',self.catalogue)
        self.current=self.root/'assets/themes/current'
        self.journal=self.state_dir/'transition.json'
        self.error=''
        self.pending=self.state_dir/'wallpaper-pending.json'

    def _guard(self):
        require_session(self.root,self.state_dir,self.preview)

    @contextmanager
    def _lock(self):
        self.state_dir.mkdir(parents=True,exist_ok=True)
        path=self.state_dir/'appearance.lock'
        fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX)
            yield
        finally:os.close(fd)

    def _command(self,args):
        result=self.runner(args,capture_output=True,text=True,check=True,timeout=8)
        if result.returncode:raise RuntimeError(result.stderr or 'Не удалось обновить компонент')
        return result.stdout

    def _link(self,target):
        link=self.current.with_name('.appearance-link-'+uuid.uuid4().hex)
        try:
            link.symlink_to(target)
            os.replace(link,self.current)
        finally:
            if link.is_symlink():link.unlink()

    def _recover(self):
        if not self.journal.exists():return
        data=json.loads(self.journal.read_text())
        old=Path(data['old_target'])
        if not old.is_absolute():old=self.current.parent/old
        resolved=old.resolve()
        if data['root']!=str(self.root) or not (resolved.is_relative_to(self.root) or resolved.is_relative_to(self.state_dir)):
            raise ValueError('Некорректный журнал перехода оформления')
        previous=self.store.validate(data['previous'])
        if not (data.get('directory_move') and not old.exists() and self.current.is_dir() and not self.current.is_symlink()):
            self._link(data['old_target'])
        if data['state_existed']:self.store._write(self.store.path,previous)
        elif self.store.path.exists():self.store.path.unlink()
        self.journal.unlink()
        self._reload()

    def snapshot(self):
        if self.journal.exists():
            self._guard()
            with self._lock():self._recover()
        error=self.error;state_error=False
        try:selection=self.store.load()
        except ValueError as exc:
            selection=initial_selection(self.catalogue);error=str(exc);state_error=True
        themes=[]
        for t in self.catalogue.themes():
            colors={}
            for mode in t['modes']:
                p=resolve_palette(self.catalogue,t['id'],mode)
                colors[mode or 'legacy']={k:p[k] for k in ('bg','fg','accent')}
            themes.append(dict(t,colors=colors))
        wallpapers=[]
        for w in self.catalogue.wallpapers():
            thumb=self.state_dir/'thumbnails'/(w['sha256']+'.png')
            wallpapers.append(dict(w,thumbnail_url=thumb.as_uri() if thumb.exists() else ''))
        colors=resolve_palette(self.catalogue,selection['palette_id'],selection['mode'],selection['accent_id']) if selection['palette_id'] else {}
        requested=None
        if self.pending.exists():
            try:
                requested=json.loads(self.pending.read_text())['requested']
                self.catalogue.wallpaper(requested)
                if not error:error='Смена обоев не подтверждена. Можно проверить фон или повторно выбрать изображение.'
            except (OSError,ValueError,KeyError):error='Журнал смены обоев повреждён'
        backup=self.store.path.with_suffix('.json.bak')
        can_restore=backup.is_file() and not backup.is_symlink()
        return dict(selection=selection,themes=themes,wallpapers=wallpapers,preview=self.preview,
            enabled=session_enabled(self.root,self.state_dir,self.preview),wallpaper_status='unconfirmed' if self.pending.exists() else 'confirmed',requested_wallpaper_id=requested,
            state_error=state_error,can_restore=can_restore,
            colors={k:colors[k] for k in ('bg','fg','accent','surface') if k in colors},error=error)

    def thumbnail(self,identifier):
        self._guard()
        item=self.catalogue.wallpaper(identifier)
        folder=self.state_dir/'thumbnails';folder.mkdir(parents=True,exist_ok=True)
        out=folder/(item['sha256']+'.png')
        if not out.exists():
            from PIL import Image
            with Image.open(item['path']) as image:
                image.seek(0)
                image=image.convert('RGB');image.thumbnail((520,320))
                fd,name=tempfile.mkstemp(suffix='.png',dir=folder)
                os.close(fd)
                try:
                    image.save(name,'PNG');os.replace(name,out)
                finally:
                    if Path(name).exists():Path(name).unlink()
        return out.as_uri()

    def _reload(self):
        profile=self.root/'alacritty/niri.toml'
        if profile.exists():profile.touch()
        if not self.preview:
            (self.root/'niri/config.kdl').touch()
            self._command(['makoctl','reload'])

    def _palette(self,previous,selection):
        generation=self.state_dir/'generations'/uuid.uuid4().hex
        generation.mkdir(parents=True)
        for name,content in render_theme(self.catalogue,selection).items():
            (generation/name).write_bytes(content)
        self._command(['niri','validate','-c',str(generation/'niri-runtime.kdl')])
        directory_move=not self.current.is_symlink()
        if not directory_move:old=os.readlink(self.current)
        else:
            saved=self.current.with_name('.appearance-original-current')
            if saved.exists():raise ValueError('Временная копия прежней темы уже существует')
            old=str(saved)
        self.store._write(self.journal,dict(root=str(self.root),old_target=old,
            previous=previous,state_existed=self.store.path.exists(),directory_move=directory_move))
        try:
            if directory_move:self.current.rename(saved)
            self._link(str(generation))
            self.store.save(selection)
            self._reload()
            self.journal.unlink()
        except Exception:
            self._recover()
            raise

    def _apply_locked(self,fields):
        previous=self.store.load()
        selected=self.store.change(previous,**fields)
        if {'palette_id','mode','accent_id'}.intersection(fields):
            palette_selection=dict(selected,wallpaper_id=previous['wallpaper_id'])
            self._palette(previous,palette_selection)
            previous=palette_selection
        if 'wallpaper_id' in fields:
            item=self.catalogue.wallpaper(selected['wallpaper_id'])
            self.store._write(self.pending,dict(requested=selected['wallpaper_id']))
            try:
                self._command(['awww','img','--transition-type','none',str(item['path'])])
                self._confirm_wallpaper_locked()
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
                self.error='Не удалось подтвердить смену обоев: '+str(exc)

    def _confirm_wallpaper_locked(self):
        data=json.loads(self.pending.read_text())
        item=self.catalogue.wallpaper(data['requested'])
        query=self._command(['awww','query'])
        if 'image: '+str(item['path']) not in query:
            raise RuntimeError('Служба обоев пока не подтвердила выбранное изображение')
        previous=self.store.load()
        self.store.save(self.store.change(previous,wallpaper_id=item['id']))
        self.pending.unlink()
        if not self.preview:
            # Cache work is optional and runs after confirmation, never before sleep.
            def prepare_lock_background():
                try:
                    subprocess.run(['bash',str(self.root/'gtklock/scripts/blur-background.sh')],
                        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30,check=False)
                except (OSError,subprocess.SubprocessError):pass
            threading.Thread(target=prepare_lock_background,daemon=True).start()

    def confirm_wallpaper(self):
        self._guard();self.error=''
        with self._lock():
            try:
                if self.pending.exists():self._confirm_wallpaper_locked()
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
                self.error='Не удалось подтвердить фон: '+str(exc)
        return self.snapshot()

    def restore_backup(self):
        self._guard();self.error=''
        with self._lock():
            self._recover()
            selection=self.store.restore_backup()
            fields={k:selection[k] for k in ('palette_id','mode','accent_id') if selection['palette_id'] is not None}
            if selection['wallpaper_id'] is not None:fields['wallpaper_id']=selection['wallpaper_id']
            if fields:self._apply_locked(fields)
        return self.snapshot()

    def select(self,fields):
        self._guard();self.error=''
        with self._lock():
            self._recover()
            self._apply_locked(fields)
        return self.snapshot()
