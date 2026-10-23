#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'quickshell'))
from system_metrics import Sampler
class MetricsTests(unittest.TestCase):
 def test_cpu_delta_memory_and_missing_samples(self):
  with tempfile.TemporaryDirectory() as folder:
   proc=Path(folder)
   (proc/'stat').write_text('cpu  100 0 100 800 0 0 0 0 0 0\n')
   (proc/'meminfo').write_text('MemTotal: 10000 kB\nMemAvailable: 4000 kB\nSwapTotal: 2000 kB\nSwapFree: 1500 kB\n')
   (proc/'uptime').write_text('3661.0 8000\n');(proc/'loadavg').write_text('1.25 0.50 0.10 1/200 2\n')
   sampler=Sampler(proc)
   first=sampler.sample();self.assertIsNone(first['cpu']);self.assertEqual(first['memory'],60)
   self.assertEqual(first['swap'],25);self.assertEqual(first['uptime'],3661);self.assertEqual(first['load'],1.25)
   (proc/'stat').write_text('cpu  125 0 125 850 0 0 0 0 0 0\n')
   self.assertEqual(sampler.sample()['cpu'],50)
   self.assertIsNone(sampler.sample()['cpu'])
   (proc/'stat').write_text('cpu  1 0 1 8 0 0 0 0 0 0\n')
   self.assertIsNone(sampler.sample()['cpu'])
 def test_missing_data_is_unavailable_not_zero(self):
  with tempfile.TemporaryDirectory() as folder:
   result=Sampler(Path(folder)).sample()
   self.assertIsNone(result['cpu']);self.assertIsNone(result['memory']);self.assertIsNone(result['uptime'])
if __name__=='__main__':unittest.main()
