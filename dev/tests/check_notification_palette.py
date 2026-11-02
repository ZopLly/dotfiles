import sys
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'quickshell'))
from appearance.catalog import Catalogue
from appearance.palette import resolve_palette
from appearance.render import render_theme
c=Catalogue(ROOT)
for t in c.themes():
 for mode in t['modes']:
  p=resolve_palette(c,t['id'],mode)
  out=render_theme(c,dict(palette_id=t['id'],mode=mode,accent_id=None))['mako.conf'].decode()
  for role,key in [('bg','background-color'),('fg','text-color'),('accent','border-color')]:
   assert key+'='+p[role] in out,(t['id'],key)
print('Notification colors match all theme variants')
