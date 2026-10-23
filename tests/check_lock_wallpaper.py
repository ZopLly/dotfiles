#!/usr/bin/env python3
import hashlib, os, sys, tempfile, unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'quickshell'))
from appearance.catalog import Catalogue
from appearance.store import Store
try:
    from appearance.wallpaper_start import resolve_wallpaper, lock_background
except SystemExit as exc:
    raise AssertionError("wallpaper resolver exits during import") from exc
class LockWallpaperTests(unittest.TestCase):
    def test_independent_selection_and_cached_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);state=base/'appearance.json';cache=base/'cache';cache.mkdir()
            catalogue=Catalogue(ROOT);store=Store(state,catalogue)
            before=store.load();item=catalogue.wallpapers()[-1]
            store.save(store.change(before,wallpaper_id=item['id']))
            source=resolve_wallpaper(ROOT,state)
            self.assertEqual(source,catalogue.wallpaper(item['id'])['path'])
            self.assertEqual(lock_background(ROOT,state,cache),source)
            target=cache/('gtklock-wallpaper-'+hashlib.sha256(source.read_bytes()).hexdigest()+'.jpg')
            target.write_bytes(b'cached')
            self.assertEqual(lock_background(ROOT,state,cache),target)
            # Colour-only changes keep exactly the same background/cache key.
            store.save(store.change(store.load(),palette_id='hyprstack:catppuccin',mode='light'))
            self.assertEqual(lock_background(ROOT,state,cache),target)
            state.write_text('broken JSON')
            self.assertTrue(resolve_wallpaper(ROOT,state).is_file())
if __name__=='__main__':unittest.main()
