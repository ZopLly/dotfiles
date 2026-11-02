#!/usr/bin/env python3
"""Verify the audio visualizer stops its own child without touching other CAVA instances."""
import os
import json
from pathlib import Path
import subprocess
import tempfile
import time

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='niri-cava-test-') as temp:
    folder = Path(temp)
    cava = folder/'cava'
    cava.write_text('''#!/usr/bin/env python3
import os,time
from pathlib import Path
Path(os.environ['TEST_CAVA_PID']).write_text(str(os.getpid()))
while True:
 print('1;2;3;4;5;6;7;0;1;2;', flush=True)
 time.sleep(.05)
''')
    cava.chmod(0o755)
    env = dict(os.environ, PATH=temp+os.pathsep+os.environ['PATH'], XDG_RUNTIME_DIR=temp, TEST_CAVA_PID=str(folder/'pid'))
    worker = subprocess.Popen(['python3', str(root/'quickshell/cava_stream.py'), '--json'], env=env, stdout=subprocess.PIPE, text=True)
    try:
        levels = json.loads(worker.stdout.readline())
        assert isinstance(levels, list) and len(levels) == 20
        assert all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in levels)
        assert levels[:3] == [0.01, 0.02, 0.03]
        pid = int((folder/'pid').read_text())
        worker.terminate()
        worker.wait(timeout=4)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        else:
            raise AssertionError('CAVA child still alive')
        assert not list(folder.glob('niri-cava-*'))
    finally:
        if worker.poll() is None:
            worker.kill(); worker.wait()
print('PASS: visualizer output, child termination and temporary-file cleanup')
