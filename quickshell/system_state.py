"""Read-only adapters. Locale-independent output; never request NM secrets."""
import json
import re
from pathlib import Path


def nm_fields(line):
    """Split nmcli's escaped terse output, including colons in SSIDs."""
    fields, value, escaped = [], '', False
    for char in line:
        if escaped:
            value += char
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            fields.append(value)
            value = ''
        else:
            value += char
    fields.append(value)
    return fields


def wifi_state(optional):
    radio = optional(['nmcli', 'radio', 'wifi'])
    rows = optional(['nmcli', '-t', '-f', 'IN-USE,SSID,SIGNAL,BSSID,SECURITY', 'device', 'wifi', 'list', '--rescan', 'no'])
    networks = []
    for line in rows.splitlines():
        values = nm_fields(line)
        if len(values) != 5:
            continue
        active, ssid, signal, bssid, security = values
        networks.append(dict(ssid=ssid or 'Скрытая сеть', signal=int(signal) if signal.isdigit() else 0,
                             bssid=bssid, security=security, active=active == '*'))
    connected = next((n for n in networks if n['active']), None)
    device_rows = optional(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'device']).splitlines()
    device = next((r for line in device_rows if len(r := nm_fields(line)) == 3 and r[1] == 'wifi'), ['', '', 'unavailable'])
    connection_state = 'connecting' if device[2].startswith('connecting') else 'connected' if connected else 'disconnected'
    return dict(wifi=radio == 'enabled', wifi_available=radio in ('enabled', 'disabled'),
                wifi_device=device[0], wifi_connection_state=connection_state, wifi_connected=connected is not None, wifi_signal=connected['signal'] if connected else 0,
                network=connected['ssid'] if connected else ('Нет подключения' if radio == 'enabled' else 'Wi-Fi выключен'),
                networks=sorted(networks, key=lambda n: (not n['active'], -n['signal'])))


def audio_levels(optional):
    result = {}
    for key, token in (('volume', '@DEFAULT_AUDIO_SINK@'), ('mic_volume', '@DEFAULT_AUDIO_SOURCE@')):
        raw = optional(['wpctl', 'get-volume', token])
        match = re.search(r'Volume:\s*([\d.]+)', raw)
        result[key] = round(float(match[1])*100) if match else -1
        result['muted' if key == 'volume' else 'mic_muted'] = 'MUTED' in raw
    return result


def audio_devices(optional):
    result = {}
    for kind in ('sink', 'source'):
        default = optional(['pactl', 'get-default-'+kind])
        try:
            devices = json.loads(optional(['pactl', '-f', 'json', 'list', kind+'s'], '[]'))
        except (ValueError, TypeError):
            devices = []
        result[kind+'s'] = [dict(name=d['name'], label=d.get('description') or d['name'], active=d['name'] == default)
                           for d in devices if isinstance(d, dict) and isinstance(d.get('name'), str)
                           and (kind != 'source' or not d['name'].endswith('.monitor'))]
    return result


def audio_state(optional):
    return dict(audio_levels(optional), **audio_devices(optional))


def bluetooth_state(optional):
    adapter = optional(['bluetoothctl', 'show'])
    paired = optional(['bluetoothctl', 'devices', 'Paired'])
    connected = optional(['bluetoothctl', 'devices', 'Connected'])
    found = optional(['bluetoothctl', 'devices'])
    devices = {}
    for raw, field in ((found, None), (paired, 'paired'), (connected, 'connected')):
        for line in raw.splitlines():
            match = re.match(r'Device ([0-9A-Fa-f:]{17}) (.+)', line)
            if match:
                device = devices.setdefault(match[1], dict(address=match[1], name=match[2], connected=False, paired=False))
                if field: device[field] = True
    return dict(bluetooth_available='Controller ' in adapter, bluetooth='Powered: yes' in adapter,
                bluetooth_devices=list(devices.values()))


def brightness(optional):
    raw = optional(['brightnessctl', '--class=backlight', '-m']).split(',')
    return int(raw[3].strip('%')) if len(raw) > 3 and raw[3].strip('%').isdigit() else -1


def backlight_signature():
    values = []
    for path in Path('/sys/class/backlight').glob('*/brightness'):
        try:
            values.append((str(path), path.read_text()))
        except OSError:
            pass
    return tuple(values)


def battery_level(percent, status):
    if percent < 0:
        return 'unavailable'
    if status == 'Charging':
        return 'charging'
    if status == 'Full':
        return 'full'
    if percent <= 5:
        return 'critical'
    if percent <= 15:
        return 'low'
    return 'discharging' if status == 'Discharging' else 'idle'
