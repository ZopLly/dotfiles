#!/usr/bin/env python3
"""Exercise concurrent lock requests with fake gtklock, never lock the desktop."""
import os
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
    base=Path(temp)
    binary=base/'bin'; binary.mkdir()
    cache=base/'cache'; cache.mkdir()
    runtime=base/'runtime'; runtime.mkdir()
    env=dict(os.environ, PATH=str(binary)+os.pathsep+os.environ['PATH'], XDG_CACHE_HOME=str(cache), XDG_RUNTIME_DIR=str(runtime), TEST_LOCK=str(base/'active'), TEST_ARGS=str(base/'args'), XDG_STATE_HOME=str(base/'state'))
    (binary/'pgrep').write_text('#!/bin/sh\ntest -f "$TEST_LOCK"\n')
    (binary/'gtklock').write_text('#!/usr/bin/env python3\nimport os,json,time\nfrom pathlib import Path\nimport sys\nif "--version" in sys.argv:\n print("gtklock v4.0.0")\n raise SystemExit(0)\nassert "--daemonize" in sys.argv\nwith open(os.environ["TEST_ARGS"]+".count", "a") as log: log.write("launch\\n")\ntry:\n os.fstat(9)\n raise AssertionError("mutex inherited by locker")\nexcept OSError: pass\ntime.sleep(.2)\nPath(os.environ["TEST_ARGS"]).write_text(json.dumps(sys.argv))\nPath(os.environ["TEST_LOCK"]).touch()\n')
    for p in binary.iterdir(): p.chmod(0o755)
    command=['bash', str(ROOT/'gtklock/scripts/lock.sh')]
    first=subprocess.Popen(command, env=env)
    second=subprocess.Popen(command+['--daemonize'], env=env)
    assert first.wait(timeout=5)==0 and second.wait(timeout=5)==0
    assert (base/"args.count").read_text().count("launch")==1
    import json
    args=json.loads((base/'args').read_text())
    assert args.count('--daemonize')==1
    themed = (ROOT/'assets/themes/current/gtklock.css').exists()
    fallback = Path(subprocess.check_output(['python3',str(ROOT/'quickshell/appearance/wallpaper_start.py')],env=env,text=True).strip())
    assert args[args.index('--background')+1]==str(fallback)
    assert args[args.index('--style')+1]==str(ROOT/'assets/themes/current/gtklock.css' if themed else ROOT/'gtklock/style.css')
    (base/'active').unlink()
    import hashlib
    cached = cache/('gtklock-wallpaper-'+hashlib.sha256(fallback.read_bytes()).hexdigest()+'.jpg')
    cached.write_text('cached image')
    subprocess.run(command, env=env, check=True)
    args=json.loads((base/'args').read_text())
    assert args[args.index('--background')+1]==str(cached)
    (base/'active').unlink()
    config=base/'config';config.mkdir();(config/'gtklock').symlink_to(ROOT/'gtklock')
    subprocess.run(['bash',str(config/'gtklock/scripts/lock.sh')],env=env,check=True)
    linked_args=json.loads((base/'args').read_text())
    assert linked_args[linked_args.index('--style')+1]==args[args.index('--style')+1]
    (base/'active').unlink()
    (binary/'gtklock').write_text('#!/bin/sh\nexit 7\n')
    assert subprocess.run(command, env=env).returncode==7
print('PASS: serialized lock requests, daemon readiness invocation, cached/fallback background, failure propagation; no real lock launched')
