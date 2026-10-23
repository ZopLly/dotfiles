#!/usr/bin/env python3
"""Mako client and JSON-lines bridge. Notification content stays in memory."""
import json
import os
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from gi.repository import Gio, GLib

class MakoClient:
    def __init__(self,bus):self.bus=bus

    def call(self,method,args=None):
        return self.bus.call_sync('org.freedesktop.Notifications','/fr/emersion/Mako',
            'fr.emersion.Mako',method,args,None,Gio.DBusCallFlags.NO_AUTO_START,1500,None).unpack()

    def snapshot(self):
        active=self.call('ListNotifications')[0]
        ids={n['id'] for n in active}
        def clean(item):
            # Icons/markup/actions from external apps never become executable UI.
            return dict(id=item['id'],app_name=item.get('app-name') or '',
                summary=item.get('summary') or '',body=item.get('body') or '',
                urgency={0:'low',1:'normal',2:'critical'}.get(item.get('urgency'),'normal'))
        return dict(available=True,active=[clean(n) for n in active[:50]],
            history=[clean(n) for n in self.call('ListHistory')[0] if n['id'] not in ids][:50],
            dnd='do-not-disturb' in self.call('ListModes')[0],error='')

    def act(self,action,value):
        if action=='dismiss' and type(value) is int and 0<value<=0xffffffff:
            self.call('DismissNotifications',GLib.Variant('(a{sv})',({'id':GLib.Variant('u',value)},)))
        elif action=='clear':
            # Explicitly dismiss each current item: never restores or deletes history.
            for item in self.call('ListNotifications')[0]:self.act('dismiss',item['id'])
        elif action=='dnd' and type(value) is bool:
            modes=list(self.call('ListModes')[0])
            modes=[m for m in modes if m!='do-not-disturb']
            if value:modes.append('do-not-disturb')
            self.call('SetModes',GLib.Variant('(as)',(modes,)))
        else:raise ValueError('Неизвестное действие уведомлений')

def main():
    from preview_scope import require_session
    root=Path(__file__).resolve().parents[1]
    state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'niri-shell'
    preview=os.environ.get('NIRI_SHELL_PREVIEW')=='1'
    def emit(data):print(json.dumps(data,ensure_ascii=False),flush=True)
    try:require_session(root,state,preview)
    except (OSError,ValueError,RuntimeError):
        emit(dict(available=False,active=[],history=[],dnd=False,error='Уведомления доступны в рабочей сессии'));return
    # Preview must never read or dismiss notifications on the user's bus.
    if preview:
        sample=dict(available=True,preview=True,dnd=False,error='',history=[],active=[
            dict(id=1,app_name='Niri · демонстрация',summary='Уведомления в одном месте',
                body='Здесь появятся сообщения приложений. Это тестовый пример; личные уведомления скрыты.',urgency='normal')])
        emit(sample)
        for line in sys.stdin:
            try:
                request=json.loads(line);action=request.get('action');value=request.get('value')
                if action=='dnd' and type(value) is bool:sample['dnd']=value
                elif action in ('dismiss','clear'):
                    removed=[n for n in sample['active'] if action=='clear' or n['id']==value]
                    sample['active']=[n for n in sample['active'] if n not in removed]
                    sample['history']=removed+sample['history']
                emit(sample)
            except (ValueError,TypeError,AttributeError):pass
        return
    bus=Gio.bus_get_sync(Gio.BusType.SESSION,None);client=MakoClient(bus)
    pending=0
    def refresh():
        nonlocal pending
        pending=0
        try:emit(client.snapshot())
        except GLib.Error:emit(dict(available=False,active=[],history=[],dnd=False,error='Служба уведомлений недоступна'))
        return False
    def changed(*args):
        nonlocal pending
        if not pending:pending=GLib.timeout_add(100,refresh)
    bus.signal_subscribe('org.freedesktop.Notifications','org.freedesktop.DBus.Properties','PropertiesChanged',
        '/fr/emersion/Mako',None,Gio.DBusSignalFlags.NONE,changed)
    bus.signal_subscribe('org.freedesktop.DBus','org.freedesktop.DBus','NameOwnerChanged',
        '/org/freedesktop/DBus','org.freedesktop.Notifications',Gio.DBusSignalFlags.NONE,changed)
    loop=GLib.MainLoop()
    def request(fd,condition):
        line=sys.stdin.readline()
        if not line:loop.quit();return False
        try:
            data=json.loads(line)
            if data.get('action')!='refresh':client.act(data.get('action'),data.get('value'))
            refresh()
        except (ValueError,TypeError,AttributeError,GLib.Error):
            emit(dict(available=False,active=[],history=[],dnd=False,error='Не удалось изменить уведомления'))
        return True
    GLib.io_add_watch(sys.stdin,GLib.IO_IN|GLib.IO_HUP,request)
    GLib.timeout_add_seconds(30,lambda:(refresh(),True)[1])
    refresh();loop.run()
if __name__=='__main__':main()
