"""Instantaneous sysfs estimate; never infer time from capacity percentage."""
from pathlib import Path


def estimate(path, status):
    unknown=dict(remaining_seconds=None,remaining_text='')
    if status!='Discharging':return unknown
    path=Path(path)
    for stored,rate in [('energy_now','power_now'),('charge_now','current_now')]:
        try:
            energy=int((path/stored).read_text());power=int((path/rate).read_text())
            if energy<0 or power<=0:continue
            seconds=energy*3600//power
            minutes=seconds//60
            if minutes<1:text='менее 1 мин до разряда'
            else:
                hours,minutes=divmod(minutes,60)
                duration=(str(hours)+' ч'+(' '+str(minutes)+' мин' if minutes else '')) if hours else str(minutes)+' мин'
                text='≈ '+duration+' до разряда'
            return dict(remaining_seconds=seconds,remaining_text=text)
        except (OSError,ValueError):continue
    return unknown
