#!/usr/bin/env python3
"""A media player on the private preview bus, for integration checks only."""
import json
import sys
from pathlib import Path
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

XML = '''<node><interface name="org.mpris.MediaPlayer2">
<method name="Raise"/><method name="Quit"/>
<property name="CanQuit" type="b" access="read"/><property name="CanRaise" type="b" access="read"/>
<property name="HasTrackList" type="b" access="read"/><property name="Identity" type="s" access="read"/>
<property name="DesktopEntry" type="s" access="read"/><property name="SupportedUriSchemes" type="as" access="read"/>
<property name="SupportedMimeTypes" type="as" access="read"/></interface>
<interface name="org.mpris.MediaPlayer2.Player">
<method name="Next"/><method name="Previous"/><method name="PlayPause"/><method name="Play"/><method name="Pause"/><method name="Stop"/>
<method name="Seek"><arg type="x" direction="in"/></method>
<method name="SetPosition"><arg type="o" direction="in"/><arg type="x" direction="in"/></method>
<property name="PlaybackStatus" type="s" access="read"/><property name="LoopStatus" type="s" access="readwrite"/>
<property name="Rate" type="d" access="readwrite"/><property name="Shuffle" type="b" access="readwrite"/>
<property name="Metadata" type="a{sv}" access="read"/><property name="Volume" type="d" access="readwrite"/>
<property name="Position" type="x" access="read"/><property name="MinimumRate" type="d" access="read"/>
<property name="MaximumRate" type="d" access="read"/><property name="CanGoNext" type="b" access="read"/>
<property name="CanGoPrevious" type="b" access="read"/><property name="CanPlay" type="b" access="read"/>
<property name="CanPause" type="b" access="read"/><property name="CanSeek" type="b" access="read"/>
<property name="CanControl" type="b" access="read"/></interface></node>'''
status = 'Playing'
position = 30000000
connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
log = Path(sys.argv[1])

def getter(_connection, _sender, _path, interface, name):
    if name == 'Metadata':
        return GLib.Variant('a{sv}', {'mpris:trackid': GLib.Variant('o', '/track/1'), 'mpris:length': GLib.Variant('x', 180000000), 'xesam:title': GLib.Variant('s', 'Тестовый трек'), 'xesam:artist': GLib.Variant('as', ['Проверка MPRIS'])})
    values = {'Identity': ('s','Тестовый плеер'), 'DesktopEntry':('s','preview'), 'PlaybackStatus':('s',status), 'Position':('x',position), 'LoopStatus':('s','None'), 'Rate':('d',1.), 'Volume':('d',.5), 'MinimumRate':('d',1.), 'MaximumRate':('d',1.), 'SupportedUriSchemes':('as',[]), 'SupportedMimeTypes':('as',[]), 'HasTrackList':('b',False), 'Shuffle':('b',False)}
    return GLib.Variant(*values.get(name, ('b',True)))

def method(_c, _s, _p, _i, name, parameters, invocation):
    global status, position
    with log.open('a') as file: file.write(json.dumps({'method':name, 'args':parameters.unpack()})+'\n')
    if name == 'Pause': status = 'Paused'
    if name == 'Play': status = 'Playing'
    if name == 'Stop': status = 'Stopped'
    if name == 'PlayPause': status = 'Paused' if status == 'Playing' else 'Playing'
    if name == 'SetPosition': position = parameters.unpack()[1]
    if name == 'Seek': position += parameters.unpack()[0]
    connection.emit_signal(None, '/org/mpris/MediaPlayer2', 'org.freedesktop.DBus.Properties', 'PropertiesChanged', GLib.Variant('(sa{sv}as)', ('org.mpris.MediaPlayer2.Player', {'PlaybackStatus':GLib.Variant('s',status), 'Position':GLib.Variant('x',position)}, [])))
    invocation.return_value(None)

for interface in Gio.DBusNodeInfo.new_for_xml(XML).interfaces:
    connection.register_object('/org/mpris/MediaPlayer2', interface, method, getter, lambda *_: True)
Gio.bus_own_name_on_connection(connection, 'org.mpris.MediaPlayer2.preview', Gio.BusNameOwnerFlags.NONE, None, None)
GLib.MainLoop().run()
