from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='lock-layout-events-') as t:
 p=Path(t);fake=p/'niri'
 binary=p/'check-keyboard'
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','gtk+-3.0','gio-2.0','json-glib-1.0'],text=True).split()
 subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/'dev/tests/check_lock_keyboard.c'),'-o',str(binary),*flags],check=True)
 fake.write_text('''#!/usr/bin/python3
import json,os,time
from pathlib import Path
Path(os.environ['LOCK_TEST_PID']).write_text(str(os.getpid()))
print(json.dumps({'KeyboardLayoutsChanged':{'keyboard_layouts':{'names':['English (US)','Russian'],'current_idx':0}}}),flush=True)
time.sleep(.25)
print(json.dumps({'KeyboardLayoutSwitched':{'idx':1}}),flush=True)
time.sleep(30)
''');fake.chmod(0o755)
 env=dict(os.environ,PATH=t+os.pathsep+os.environ['PATH'],LOCK_TEST_PID=str(p/'pid'))
 subprocess.run(['xvfb-run','-a',str(binary),'--stream'],env=env,check=True)
 pid=int((p/'pid').read_text())
 try:os.kill(pid,0)
 except ProcessLookupError:pass
 else:raise AssertionError('Layout stream child still running')
 print('PASS: real asynchronous reader received EN then RU; child terminated and reaped')
