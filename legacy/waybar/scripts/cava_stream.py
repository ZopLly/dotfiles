#!/usr/bin/env python3
"""Own and clean up one CAVA process and its temporary configuration."""
import os
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

json_output = "--json" in sys.argv
child = None

def stop(*_):
    raise SystemExit(0)

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
try:
    with tempfile.NamedTemporaryFile(mode='w', prefix='niri-cava-', dir=os.environ.get('XDG_RUNTIME_DIR') or None) as config:
        config.write(f'''[general]
bars = {20 if json_output else 10}
framerate = {20 if json_output else 30}
sleep_timer = 1
[input]
method = pulse
[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = {100 if json_output else 7}
''')
        config.flush()
        child = subprocess.Popen(['cava', '-p', config.name], stdout=subprocess.PIPE, text=True)
        for line in child.stdout:
            values = [int(v) for v in line.strip().split(';') if v.isdigit()]
            if json_output:
                levels = [max(0, min(100, v))/100 for v in values[:20]]
                print(json.dumps(levels + [0]*(20-len(levels))), flush=True)
                continue
            bars = ''.join('  ▂▃▄▅▆▇'[min(v,7)] for v in values)
            print(bars if bars.strip() else '󰎈', flush=True)
except BrokenPipeError:
    sys.stdout = open(os.devnull, 'w')
finally:
    if child and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
