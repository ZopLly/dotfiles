import importlib.util
from pathlib import Path
from datetime import date
from unittest.mock import patch
import unittest
import tempfile
spec=importlib.util.spec_from_file_location('calendar_service', Path(__file__).resolve().parents[2]/'quickshell/calendar_service.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
ICS=b'''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Calendar//EN
BEGIN:VEVENT
UID:repeat
DTSTART:20260918T220000Z
DTEND:20260918T230000Z
RRULE:FREQ=DAILY;COUNT=3
EXDATE:20260919T220000Z
SUMMARY:Recurring meeting
END:VEVENT
BEGIN:VEVENT
UID:holiday
DTSTART;VALUE=DATE:20260918
DTEND;VALUE=DATE:20260920
SUMMARY:Two days
END:VEVENT
BEGIN:VEVENT
UID:cancelled
DTSTART:20260918T100000Z
STATUS:CANCELLED
SUMMARY:Cancelled
END:VEVENT
END:VCALENDAR
'''
class CalendarTests(unittest.TestCase):
 def test_dates_recurrence_exclusion_and_cancelled(self):
  events=c.normalize(ICS,date(2026,9,18))['events']
  repeat=[e for e in events if e['title']=='Recurring meeting']
  self.assertEqual([e['date'] for e in repeat],['2026-09-19','2026-09-21'])
  self.assertEqual(repeat[0]['time'],'01:00')
  self.assertEqual([e['date'] for e in events if e['allDay']],['2026-09-18','2026-09-19'])
  self.assertFalse(any(e['title']=='Cancelled' for e in events))
 def test_urls_restricted(self):
  self.assertTrue(c.valid_url('https://calendar.google.com/calendar/ical/test/private-token/basic.ics'))
  for url in ('http://calendar.google.com/calendar/ical/a.ics','https://evil.com/calendar/ical/a.ics','file:///tmp/a.ics','https://name@calendar.google.com/calendar/ical/a.ics'):
   self.assertFalse(c.valid_url(url))
 def test_preview_never_reads_secret(self):
  with patch.dict(c.os.environ,{'NIRI_SHELL_PREVIEW':'1'}), patch.object(Path,'read_text') as read:
   c.main();read.assert_not_called()
 def test_error_does_not_reveal_url(self):
  with tempfile.TemporaryDirectory() as temp, patch.object(c,'CONFIG',Path(temp)/'url'), patch.dict(c.os.environ,{'NIRI_SHELL_PREVIEW':'0'}), patch.object(c,'emit') as emit, patch.object(c.time,'sleep',side_effect=InterruptedError), patch.object(c,'build_opener',side_effect=RuntimeError('secret-token')):
   c.CONFIG.write_text('https://calendar.google.com/calendar/ical/test/private-secret-token/basic.ics');c.CONFIG.chmod(0o600)
   with self.assertRaises(InterruptedError):c.main()
   self.assertNotIn('secret-token',str(emit.call_args_list))
unittest.main()
