#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
tree=ET.parse(ROOT/'gtklock/layout.xml')
objects={o.get('id'):o for o in tree.iter('object') if o.get('id')}
for name in ('window-box','info-box','time-box','clock-label','date-label','body-revealer','body-grid','input-label','input-field','message-box','message-revealer','message-scrolled-window','unlock-button','warning-label','error-label','split-columns','auth-card','lock-footer'):
 assert name in objects,name
props={p.get('name'):p.text for p in objects['input-field'].findall('property')}
assert props['visibility']=='0' and props['input-purpose']=='password'
assert any(s.get('name')=='activate' and s.get('handler')=='window_pw_check' for s in objects['input-field'].findall('signal'))
assert any(s.get('name')=='clicked' and s.get('handler')=='window_pw_check' for s in objects['unlock-button'].findall('signal'))
assert any(s.get('name')=='icon-release' and s.get('handler')=='window_pw_toggle_vis' for s in objects['input-field'].findall('signal'))
print('PASS: split layout IDs and existing password handlers preserved')
