#!/usr/bin/env python3
"""Moscow forecast, Open-Meteo; independent of the shell control backend."""
import json
import math
import os
from pathlib import Path
import time
from urllib.request import urlopen

URL = ('https://api.open-meteo.com/v1/forecast?latitude=55.7558&longitude=37.6173'
       '&current=temperature_2m,apparent_temperature,weather_code'
       '&daily=weather_code,temperature_2m_max,temperature_2m_min'
       '&temperature_unit=celsius&timezone=Europe%2FMoscow&forecast_days=3')
CACHE = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home()/'.cache'))) / 'niri-shell/weather-moscow.json'


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Invalid weather value')
    return round(value)


def parse(data):
    current, daily = data['current'], data['daily']
    days = []
    for i, date in enumerate(daily['time'][:3]):
        days.append(dict(date=date, code=number(daily['weather_code'][i]), low=number(daily['temperature_2m_min'][i]), high=number(daily['temperature_2m_max'][i])))
    return dict(temperature=number(current['temperature_2m']), feels=number(current['apparent_temperature']), code=number(current['weather_code']), days=days, updated=current['time'], fetched=time.time(), stale=False)


def emit(data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def main():
    if os.environ.get('NIRI_SHELL_PREVIEW') == '1':
        emit(dict(temperature=12, feels=10, code=3, updated='2026-09-18T12:00', stale=False, preview=True,
                  days=[dict(date='2026-09-18', code=3, low=8, high=14), dict(date='2026-09-19', code=61, low=7, high=13), dict(date='2026-09-20', code=2, low=9, high=16)]))
        return
    last = {}
    cache_delay = 0
    try:
        cache = json.loads(CACHE.read_text())
        last = parse(cache['raw'])
        last['fetched'] = cache['fetched']
        age = max(0, time.time()-float(last['fetched']))
        emit(dict(last, stale=age >= 900))
        cache_delay = max(0, 900-age)
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        pass
    if cache_delay:
        time.sleep(cache_delay)
    while True:
        try:
            with urlopen(URL, timeout=10) as response:
                raw = json.loads(response.read(131072))
            result = parse(raw)
            last = result
            emit(result)
            try:
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                temp = CACHE.with_suffix('.tmp')
                temp.write_text(json.dumps(dict(raw=raw, fetched=result['fetched'])))
                temp.replace(CACHE)
            except OSError:
                pass
            time.sleep(900)
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            emit(dict(last, stale=True, error='Не удалось обновить погоду'))
            time.sleep(300)


if __name__ == '__main__':
    main()
