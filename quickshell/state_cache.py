"""Thread-safe subsystem cache; event invalidations cannot be lost during a read."""
import threading
import time


class StateCache:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.values = {}
        self.generations = {}

    def invalidate(self, names=None):
        with self.lock:
            for name in (set(self.values) | set(self.generations)) if names is None else names:
                self.generations[name] = self.generations.get(name, 0)+1

    def get(self, name, loader, ttl=30):
        with self.lock:
            generation = self.generations.setdefault(name, 0)
            cached = self.values.get(name)
            if cached and cached[2] == generation and self.clock()-cached[1] < ttl:
                return cached[0]
        value = loader()
        with self.lock:
            self.values[name] = (value, self.clock(), generation)
        return value


AUDIO = {'audio_levels', 'audio_devices'}
NETWORK = {'wifi', 'vpns'}


def action_scopes(name):
    if name in ('volume', 'mute', 'mic-volume', 'mic-mute'):
        return {'audio_levels'}
    if name in ('audio-sink', 'audio-source'):
        return AUDIO
    if name in ('wifi', 'wifi-rescan', 'wifi-connect', 'wifi-disconnect', 'vpn'):
        return NETWORK
    if name in ('bluetooth', 'bluetooth-device', 'bluetooth-scan', 'bluetooth-pair'):
        return {'bluetooth'} | AUDIO
    return {'brightness': {'brightness'}, 'dnd': {'dnd'}, 'profile': {'power'},
            'workspace': {'niri'}, 'layout': {'niri'}}.get(name, set())


def event_scopes(stream, line):
    if stream == 'audio':
        import re
        match = re.search(r"Event '(new|change|remove)' on (sink|source|server|card) #", line)
        if not match:
            return set()  # Clients created by our own reads must not invalidate state.
        return AUDIO if match[1] != 'change' or match[2] in ('server', 'card') else {'audio_levels'}
    if stream in ('bluetooth', 'power', 'dnd'):
        if not line.startswith('signal '):
            return set()  # dbus-monitor emits several text lines per signal.
        if stream == 'power':
            return {'power'} if 'PowerProfiles;' in line or '/net/hadess/PowerProfiles;' in line else {'battery'}
        return {stream}
    if stream == 'network':
        return NETWORK
    if stream == 'niri':
        return {'niri'}
    return set()
