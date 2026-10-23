#!/usr/bin/env python3
"""Bounded refresh and race regressions; no live hardware or control commands."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quickshell'))
import backend
from state_cache import StateCache, action_scopes, event_scopes

class PerformanceTests(unittest.TestCase):
    def test_volume_event_does_not_poll_other_services(self):
        calls=[]
        def read(args,default=''):
            calls.append(args)
            if args[0]=='wpctl':return 'Volume: 0.44'
            return default
        cache=StateCache()
        with patch.object(backend,'CACHE',cache),patch.object(backend,'PREVIEW',False),patch.object(backend,'optional',side_effect=read):
            first=backend.snapshot();self.assertEqual(len(calls),22)
            calls.clear();self.assertEqual(backend.snapshot(),first);self.assertEqual(calls,[])
            cache.invalidate(event_scopes('audio',"Event 'change' on sink #55"))
            backend.snapshot();self.assertEqual([c[0] for c in calls],['wpctl','wpctl'])
            calls.clear();cache.invalidate({'brightness'});backend.snapshot()
            self.assertEqual([c[0] for c in calls],['brightnessctl'])
            calls.clear();cache.invalidate({'niri'});backend.snapshot()
            self.assertEqual([c[0] for c in calls],['niri']*3)
            calls.clear();cache.invalidate({'power'});backend.snapshot()
            self.assertEqual(calls,[['powerprofilesctl','get']])

    def test_no_event_feedback_from_our_audio_clients(self):
        for line in ("Event 'new' on client #100", "Event 'remove' on client #100", "Event 'change' on sink-input #10"):
            self.assertFalse(event_scopes('audio',line))
        self.assertEqual(event_scopes('audio',"Event 'new' on sink #1"),{'audio_levels','audio_devices'})

    def test_one_dbus_invalidation_per_header(self):
        self.assertEqual(event_scopes('power','signal time=1 path=/org/freedesktop/UPower/PowerProfiles; interface=org.freedesktop.DBus.Properties;'),{'power'})
        self.assertEqual(event_scopes('power','signal time=1 path=/org/freedesktop/UPower/devices/battery_BAT0; interface=org.freedesktop.DBus.Properties;'),{'battery'})
        self.assertEqual(event_scopes('power','   string "ActiveProfile"'),set())
        self.assertEqual(event_scopes('bluetooth','signal time=1 path=/org/bluez/hci0;'),{'bluetooth'})
        self.assertEqual(action_scopes('save-widget'),set())
        self.assertEqual(action_scopes('workspace'),{'niri'})

    def test_event_arriving_during_loader_is_not_lost(self):
        cache=StateCache();count=0
        def load():
            nonlocal count
            count+=1
            if count==1:cache.invalidate()
            return count
        self.assertEqual(cache.get('audio',load),1)
        self.assertEqual(cache.get('audio',load),2)
        self.assertEqual(cache.get('audio',load),2)

    def test_fallback_refresh_after_ttl(self):
        now=[0.];cache=StateCache(clock=lambda:now[0]);values=iter((1,2))
        self.assertEqual(cache.get('power',lambda:next(values)),1)
        now[0]=29.;self.assertEqual(cache.get('power',lambda:next(values)),1)
        now[0]=30.;self.assertEqual(cache.get('power',lambda:next(values)),2)

unittest.main()
