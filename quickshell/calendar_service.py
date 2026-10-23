#!/usr/bin/env python3
"""Read-only Google iCal feed. Never log the private URL or event payload."""
import json
import os
from pathlib import Path
import time
from datetime import date, datetime, time as daytime, timedelta
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Europe/Moscow')
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'niri-shell/google-calendar.url'

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def valid_url(url):
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and parsed.hostname == 'calendar.google.com'
            and parsed.port in (None,443) and not parsed.username and not parsed.password
            and parsed.path.startswith('/calendar/ical/') and parsed.path.endswith('.ics')
            and not parsed.query and not parsed.fragment)


def normalize(raw, today=None):
    import icalendar
    import recurring_ical_events
    today = today or datetime.now(ZONE).date()
    first, last = today-timedelta(days=31), today+timedelta(days=183)
    start = datetime.combine(first, daytime.min, ZONE)
    end = datetime.combine(last, daytime.min, ZONE)
    calendar = icalendar.Calendar.from_ical(raw)
    events = []
    for event in recurring_ical_events.of(calendar).between(start, end):
        if str(event.get('STATUS', '')).upper() == 'CANCELLED':
            continue
        begin = event.decoded('DTSTART')
        all_day = not isinstance(begin, datetime)
        finish = event.decoded('DTEND', begin + (timedelta(days=1) if all_day else timedelta()))
        def local(value):
            if not isinstance(value, datetime):
                return datetime.combine(value, daytime.min, ZONE)
            return value.replace(tzinfo=ZONE) if value.tzinfo is None else value.astimezone(ZONE)
        begin, finish = local(begin), local(finish)
        day = max(first, begin.date())
        final_day = min(last-timedelta(days=1), (finish-timedelta(microseconds=1)).date() if finish > begin else begin.date())
        while day <= final_day:
            events.append(dict(date=day.isoformat(), time=begin.strftime('%H:%M') if day == begin.date() else 'Продолжение',
                               title=str(event.get('SUMMARY', 'Без названия')), allDay=all_day))
            if len(events) > 5000:
                raise ValueError('Calendar too large')
            day += timedelta(days=1)
    events.sort(key=lambda e: (e['date'], not e['allDay'], e['time'], e['title']))
    return dict(configured=True, events=events, rangeStart=first.isoformat(), rangeEnd=(last-timedelta(days=1)).isoformat(), updated=datetime.now(ZONE).strftime('%d.%m %H:%M'), error='')


def emit(data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def main():
    if os.environ.get('NIRI_SHELL_PREVIEW') == '1':
        return
    previous = None
    previous_url = None
    while True:
        delay = 600
        try:
            if not CONFIG.exists():
                previous = previous_url = None
                emit(dict(configured=False, events=[]))
                time.sleep(15)
                continue
            url = CONFIG.read_text().strip()
            if url != previous_url:
                previous = None
                previous_url = url
            if not valid_url(url):
                raise ValueError('Invalid Google feed')
            if CONFIG.stat().st_mode & 0o077:
                emit(dict(configured=False, events=[], error='Файл календаря: нужны права 600'))
                time.sleep(15)
                continue
            try:
                import icalendar, recurring_ical_events
            except ImportError:
                emit(dict(configured=False, events=[], error='Установи библиотеки календаря: scripts/setup-calendar.sh'))
                time.sleep(30)
                continue
            with build_opener(NoRedirect()).open(url, timeout=15) as response:
                raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise ValueError('Calendar too large')
            previous = normalize(raw)
            emit(previous)
        except Exception:
            # Exceptions may contain the secret URL; never print them.
            emit(dict(previous or dict(configured=True, events=[]), error='Не удалось обновить Google Calendar'))
            delay = 60
        time.sleep(delay)


if __name__ == '__main__':
    main()
