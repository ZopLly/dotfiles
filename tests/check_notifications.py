#!/usr/bin/env python3
"""Mako integration on a private bus; never touches session notifications."""
import os, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'quickshell'))
from notifications import MakoClient
from gi.repository import Gio
if '--private' not in sys.argv:
    raise SystemExit(subprocess.call(['dbus-run-session','--',sys.executable,__file__,'--private']))
with tempfile.TemporaryDirectory() as folder:
    config=Path(folder)/'mako.conf';config.write_text('invisible=1\nmax-history=20\ndefault-timeout=0\n')
    process=subprocess.Popen(['mako','--config',str(config)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
        from gi.repository import GLib
        for _ in range(80):
            owned=bus.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',GLib.Variant('(s)',('org.freedesktop.Notifications',)),None,Gio.DBusCallFlags.NONE,1000,None).unpack()[0]
            if owned:break
            time.sleep(.05)
        else:raise AssertionError('private Mako failed to start')
        client=MakoClient(bus)
        assert client.snapshot()['active']==[]
        subprocess.run(['notify-send','-a','Niri Test','Synthetic title','<b>Synthetic body</b>'],check=True)
        state=client.snapshot();assert len(state['active'])==1,state
        item=state['active'][0];assert item['summary']=='Synthetic title'
        assert item['app_name']=='Niri Test' and item['urgency']=='normal'
        assert 'Synthetic body' in item['body']
        client.act('dnd',True);assert client.snapshot()['dnd']
        client.act('dismiss',item['id']);state=client.snapshot()
        assert not state['active'] and len(state['history'])==1,state
        client.act('dnd',False);assert not client.snapshot()['dnd']
        subprocess.run(['notify-send','-a','Niri Test','Second','Body'],check=True)
        client.act('clear',None);assert not client.snapshot()['active']
        for action,value in [('dismiss',-1),('dismiss','1'),('dnd','true'),('invoke','rm'),('invalid',None)]:
            try:client.act(action,value)
            except ValueError:pass
            else:raise AssertionError('unsafe action accepted')
    finally:
        process.terminate();process.wait(timeout=5)
print('PASS: private Mako delivery, history, DND, dismiss, clear and input validation')
