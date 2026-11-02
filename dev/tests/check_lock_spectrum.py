from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='lock-spectrum-') as t:
 p=Path(t);binary=p/'check-spectrum';fake=p/'cava'
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','gtk+-3.0','gio-2.0','json-glib-1.0'],text=True).split()
 subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/'dev/tests/check_lock_spectrum.c'),'-o',str(binary),*flags],check=True)
 fake.write_text('''#!/usr/bin/python3
import os,time
from pathlib import Path
Path(os.environ['SPECTRUM_TEST_CAVA_PID']).write_text(str(os.getpid()))
while True:
 print('25;'*20,flush=True)
 time.sleep(.05)
''');fake.chmod(0o755)
 env=dict(os.environ,PATH=t+os.pathsep+os.environ['PATH'],NIRI_LOCK_ROOT=str(ROOT),GDK_BACKEND="x11",XDG_RUNTIME_DIR=t,SPECTRUM_TEST_CAVA_PID=str(p/'cava.pid'),SPECTRUM_TEST_WORKER_PID=str(p/'worker.pid'))
 subprocess.run(['xvfb-run','-a','-e','/tmp/lock-spectrum-xvfb.log',str(binary)],env=env,check=True)
 for name in ('worker.pid','cava.pid'):
  pid=int((p/name).read_text())
  try:os.kill(pid,0)
  except ProcessLookupError:pass
  else:raise AssertionError('Leaked child: '+name)
 assert not list(p.glob('niri-cava-*'))
 print('PASS: worker and CAVA reaped; temporary audio configuration removed; no real audio service used')
