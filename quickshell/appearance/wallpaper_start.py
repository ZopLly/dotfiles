#!/usr/bin/env python3
"""Resolve independent desktop/lock artwork without processing images at lock time."""
import hashlib
import os
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from appearance.catalog import Catalogue
from appearance.store import Store

def resolve_wallpaper(root,state):
    root=Path(root)
    try:
        catalogue=Catalogue(root)
        selection=Store(state,catalogue).load()
        if selection.get('wallpaper_id'):
            return catalogue.wallpaper(selection['wallpaper_id'])['path']
    except (OSError,ValueError,KeyError):pass
    for folder in (root/'assets/themes/_installed-current',root/'assets/themes/current',root/'assets/wallpapers'):
        if folder.is_dir():
            for item in sorted(folder.iterdir()):
                if item.is_file() and item.suffix.lower() in ('.png','.jpg','.jpeg','.gif','.webp'):
                    return item
    return None

def cache_target(source,cache):
    return Path(cache)/('gtklock-wallpaper-'+hashlib.sha256(Path(source).read_bytes()).hexdigest()+'.jpg')

def lock_background(root,state,cache):
    source=resolve_wallpaper(root,state)
    if source:
        target=cache_target(source,cache)
        if target.is_file() and target.stat().st_size:return target
    return source

def main():
    root=Path(__file__).resolve().parents[2]
    state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'niri-shell/appearance.json'
    cache=Path(os.environ.get('XDG_CACHE_HOME',str(Path.home()/'.cache')))
    source=lock_background(root,state,cache) if '--lock-background' in sys.argv else resolve_wallpaper(root,state)
    if source:print(source)
if __name__=='__main__':main()
