"""Versioned appearance choices, independent from widget layouts."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid
from .palette import resolve_palette

def initial_selection(catalogue):
    palette_id=None;wallpaper_id=None
    empty=dict(version=1,palette_id=None,mode=None,accent_id=None,wallpaper_id=None,revision=0)
    try:
        current=catalogue.safe('assets/themes/current')
        candidate=catalogue.safe(current/'waybar.css')
    except ValueError:return empty
    if current.exists():
        for theme in catalogue.themes():
            if theme['group']=='legacy':
                old=catalogue.legacy_file(theme['id'],'waybar.css')
                if candidate.is_file() and old.read_bytes()==candidate.read_bytes():
                    palette_id=theme['id'];break
        for p in sorted(current.iterdir()):
            if p.suffix.lower() in {'.jpg','.jpeg','.png','.webp','.gif'} and p.is_file():
                try:p=catalogue.safe(p)
                except ValueError:continue
                digest=hashlib.sha256(p.read_bytes()).hexdigest()
                wallpaper_id=next((w['id'] for w in catalogue.wallpapers() if w['sha256']==digest),None)
                break
    return dict(version=1,palette_id=palette_id,mode=None,accent_id=None,wallpaper_id=wallpaper_id,revision=0)

class Store:
    def __init__(self,path,catalogue):
        self.path=Path(path)
        self.catalogue=catalogue

    def validate(self,data):
        keys={'version','palette_id','mode','accent_id','wallpaper_id','revision'}
        if not isinstance(data,dict) or set(data)!=keys or data['version']!=1 or type(data['revision']) is not int or data['revision']<0:
            raise ValueError('Неподдерживаемый формат настроек оформления')
        if data['palette_id'] is not None:
            resolve_palette(self.catalogue,data['palette_id'],data['mode'],data['accent_id'])
        elif data['mode'] is not None or data['accent_id'] is not None:
            raise ValueError('Сначала выберите палитру')
        if data['wallpaper_id'] is not None:self.catalogue.wallpaper(data['wallpaper_id'])
        return dict(data)

    def load(self):
        if self.path.is_symlink():raise ValueError('Настройки оформления не должны быть ссылкой')
        if not self.path.exists():return initial_selection(self.catalogue)
        try:return self.validate(json.loads(self.path.read_text()))
        except (OSError,ValueError,TypeError,KeyError) as exc:
            raise ValueError('Настройки оформления повреждены; доступна резервная копия .bak') from exc

    def change(self,current,**fields):
        if not fields or not set(fields)<={'palette_id','mode','accent_id','wallpaper_id'}:
            raise ValueError('Неизвестные параметры оформления')
        result=self.validate(current)
        if 'palette_id' in fields and fields['palette_id']!=result['palette_id']:
            theme=self.catalogue.theme(fields['palette_id'])
            result.update(mode='dark' if theme['group']=='hyprstack' else None,accent_id=None)
        result.update(fields)
        result['revision']+=1
        return self.validate(result)

    def _write(self,path,data):
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.appearance-',dir=path.parent)
        try:
            with os.fdopen(fd,'w') as f:
                json.dump(data,f,ensure_ascii=False,indent=2)
                f.write('\n');f.flush();os.fsync(f.fileno())
            os.replace(name,path)
        finally:
            if Path(name).exists():Path(name).unlink()

    def save(self,data):
        data=self.validate(data)
        if self.path.is_symlink():raise ValueError('Настройки оформления не должны быть ссылкой')
        if self.path.exists():self._write(self.path.with_suffix('.json.bak'),self.load())
        self._write(self.path,data)

    def restore_backup(self):
        backup=self.path.with_suffix('.json.bak')
        if self.path.is_symlink() or backup.is_symlink():raise ValueError('Настройки не должны быть ссылкой')
        try:data=self.validate(json.loads(backup.read_text()))
        except (OSError,ValueError,TypeError,KeyError) as exc:raise ValueError('Нет корректной резервной копии') from exc
        if self.path.exists():
            preserved=self.path.with_name('appearance.corrupt-'+uuid.uuid4().hex+'.json')
            fd=os.open(preserved,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as f:f.write(self.path.read_bytes())
        self._write(self.path,data)
        return data
