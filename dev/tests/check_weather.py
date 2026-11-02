import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest
import tempfile
import json

spec=importlib.util.spec_from_file_location('weather', Path(__file__).resolve().parents[2]/'quickshell/weather.py')
w=importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
RAW={'current': {'temperature_2m': -3.2, 'apparent_temperature': -8, 'weather_code': 71, 'time':'2026-09-18T12:00'}, 'daily': {'time':['2026-09-18'], 'temperature_2m_min':[-7], 'temperature_2m_max':[-1], 'weather_code':[71]}}
class WeatherTests(unittest.TestCase):
    def test_freezing_and_missing_values(self):
        self.assertEqual(w.parse(RAW)['temperature'], -3)
        self.assertEqual(w.parse(RAW)['days'][0]['low'], -7)
        for value in (None, True, float('nan'), '12'):
            with self.assertRaises(ValueError): w.number(value)
    def test_offline_cache_retained(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(w,'CACHE',Path(temp)/'cache'), patch.dict(w.os.environ, {'NIRI_SHELL_PREVIEW':'0'}), patch.object(w,'urlopen',side_effect=OSError('offline')), patch.object(w.time,'sleep',side_effect=InterruptedError), patch.object(w,'emit') as emit:
            w.CACHE.write_text(json.dumps({'raw':RAW,'fetched':1}))
            with self.assertRaises(InterruptedError): w.main()
            result=emit.call_args.args[0]
            self.assertEqual(result['temperature'],-3)
            self.assertTrue(result['stale'])
            self.assertIn('error',result)
    def test_restart_respects_fresh_cache_interval(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(w,'CACHE',Path(temp)/'cache'), patch.dict(w.os.environ, {'NIRI_SHELL_PREVIEW':'0'}), patch.object(w,'urlopen') as fetch, patch.object(w.time,'time',return_value=1000), patch.object(w.time,'sleep',side_effect=InterruptedError) as sleep, patch.object(w,'emit') as emit:
            w.CACHE.write_text(json.dumps({'raw':RAW,'fetched':900}))
            with self.assertRaises(InterruptedError): w.main()
            fetch.assert_not_called()
            sleep.assert_called_once_with(800)
            self.assertFalse(emit.call_args.args[0]['stale'])
    def test_preview_never_connects(self):
        with patch.dict(w.os.environ, {'NIRI_SHELL_PREVIEW':'1'}), patch.object(w,'urlopen') as fetch, patch.object(w,'emit') as emit:
            w.main()
            fetch.assert_not_called()
            self.assertTrue(emit.call_args.args[0]['preview'])
unittest.main()
