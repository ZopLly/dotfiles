#!/usr/bin/env python3
import importlib
from pathlib import Path
import sys,tempfile,unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'quickshell'))
class BatteryTimeTests(unittest.TestCase):
 def estimate(self,files,status='Discharging'):
  self.assertTrue((ROOT/'quickshell/battery_time.py').exists(),'Remaining battery time not implemented')
  module=importlib.import_module('battery_time')
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)
   for name,value in files.items():(path/name).write_text(str(value))
   return module.estimate(path,status)
 def test_energy_and_charge_units_produce_hours_and_minutes(self):
  for values in ({'energy_now':30000000,'power_now':12000000},{'charge_now':3000000,'current_now':1200000}):
   result=self.estimate(values)
   self.assertEqual(result['remaining_seconds'],9000)
   self.assertEqual(result['remaining_text'],'≈ 2 ч 30 мин до разряда')
 def test_unknown_rate_and_charging_do_not_invent_an_estimate(self):
  for files,status in [({},'Discharging'),({'energy_now':1,'power_now':0},'Discharging'),({'energy_now':1,'power_now':-1},'Discharging'),({'energy_now':'bad','power_now':3},'Discharging'),({'energy_now':30,'power_now':12},'Charging')]:
   self.assertEqual(self.estimate(files,status),dict(remaining_seconds=None,remaining_text=''))
 def test_charge_fallback_and_less_than_minute(self):
  self.assertEqual(self.estimate({'energy_now':30,'power_now':0,'charge_now':3,'current_now':12})['remaining_seconds'],900)
  self.assertEqual(self.estimate({'energy_now':1,'power_now':100})['remaining_text'],'менее 1 мин до разряда')
if __name__=='__main__':unittest.main()
