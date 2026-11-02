#!/usr/bin/env python3
"""Test the real locker only on a disposable nested Niri, never the parent session."""
import json,os,pathlib,signal,subprocess,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
if len(sys.argv)>1 and sys.argv[1]=='--client':
    target=pathlib.Path(sys.argv[2]);env=dict(os.environ)
    # Niri sets a NEW Wayland socket for its child. Verify it is our nested instance.
    assert env.get('NIRI_SOCKET','').startswith(str(target/'runtime'))
    result=subprocess.run(['gtklock','--daemonize','--config',str(ROOT/'gtklock/config.ini'),'--layout',str(ROOT/'gtklock/layout.xml'),'--style',str(ROOT/'assets/themes/ancient-odyssey/gtklock.css'),'--background',str(ROOT/'assets/themes/ancient-odyssey/wallpaper.jpg'),'--modules',str(ROOT/'gtklock/modules/minimal-module.so'),'--modules',str(ROOT/'gtklock/modules/notifications-module.so'),'--modules',str(ROOT/'gtklock/modules/layout-module.so'),'--modules',str(ROOT/'gtklock/modules/keyboard-module.so'),'--modules',str(target/'geometry-probe.so')],timeout=8)
    assert result.returncode==0,'lock readiness failed'
    time.sleep(2)
    geometry=json.loads((target/'geometry.json').read_text())
    if geometry['width']>=920:
        assert geometry['card_x']>geometry['width']/2,geometry
        assert abs(geometry['card_x']+geometry['card_width']-(geometry['width']-64))<8,geometry
    assert geometry['music_visible'] and geometry['notifications_visible'],geometry
    (target/'ready').write_text('Actual gtklock v4 acquired nested session lock; custom layout/module loaded. Authentication not attempted.')
    time.sleep(30)
else:
    target=pathlib.Path(tempfile.mkdtemp(prefix='gtklock-minimal-preview-'));(target/'runtime').mkdir(mode=0o700)
    (target/'niri.kdl').write_text('output "winit" { mode "1280x800"; }\ninput { keyboard { xkb { layout "us,ru"; options "grp:alt_shift_toggle"; } } }\nhotkey-overlay { skip-at-startup; }\n')
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','gtk+-3.0'],text=True).split()
    subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',str(ROOT/'dev/tests/lock-geometry-probe.c'),'-o',str(target/'geometry-probe.so'),*flags],check=True)
    (target/'dbus.conf').write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(target/'runtime')+'</listen><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    env=dict(os.environ,NIRI_LOCK_ROOT=str(ROOT),GTKLOCK_TEST_GEOMETRY=str(target/'geometry.json'));display=pathlib.Path(env['XDG_RUNTIME_DIR'])/env['WAYLAND_DISPLAY'];env.update(XDG_RUNTIME_DIR=str(target/'runtime'),WAYLAND_DISPLAY=str(display),GDK_BACKEND='wayland',GTK_USE_PORTAL='0')
    with (target/'log').open('w') as log:
        proc=subprocess.Popen(['dbus-run-session','--config-file',str(target/'dbus.conf'),'--','niri','-c',str(target/'niri.kdl'),'--',sys.executable,str(pathlib.Path(__file__).resolve()),'--client',str(target)],env=env,stdout=log,stderr=log,start_new_session=True)
        try:
            for _ in range(120):
                if (target/'ready').exists() or proc.poll() is not None:break
                time.sleep(.1)
            if not (target/'ready').exists():raise RuntimeError('Nested locker test failed: '+str(target/'log'))
            print((target/'ready').read_text());print('Logs:',target/'log')
        finally:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
