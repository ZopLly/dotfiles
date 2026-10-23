#!/usr/bin/env python3
"""Acceptance test for ONLY a disposable applications preview supplied by path."""
import json,os,subprocess,sys,time
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quickshell'))
from preview_scope import require_preview


def run(base):
    base=Path(base).resolve();runtime=base/'runtime'
    env=dict(os.environ,XDG_RUNTIME_DIR=str(runtime),NIRI_SOCKET=str(next(runtime.glob('niri.*.sock'))),NIRI_SHELL_PREVIEW='1')
    with patch.dict(os.environ,env):require_preview(base/'config',base/'state/niri-shell',True)
    def command(args):return subprocess.check_output(args,env=env,text=True,stderr=subprocess.DEVNULL,timeout=8)
    def action(name,*args):return command(['niri','msg','action',name,*map(str,args)])
    def windows():return json.loads(command(['niri','msg','-j','windows']))
    def rpc(method,*args):return command(['qs','ipc','-p',str(base/'config/quickshell'),'call','applications',method,*args]).strip()
    def wait(predicate,timeout=10):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            status=json.loads(rpc('status'))
            if not status['busy'] and status['error']:raise RuntimeError(status['error'])
            if not status['busy'] and predicate():return
            time.sleep(.1)
        raise RuntimeError('Window mode was not confirmed')
    def snap():return {w['id']:(w['workspace_id'],w['is_floating'],w['layout']['pos_in_scrolling_layout'],w['layout']['window_size']) for w in windows()}
    def toggle():rpc('act','workspace-mode','winit')
    def check(before):
        wait(lambda:all(not w['is_floating'] for w in windows() if w['id'] in before))
        time.sleep(.4);after=snap()
        assert {k:v[:3] for k,v in before.items()}=={k:after[k][:3] for k in before},(before,after)
        assert all(abs(before[k][3][i]-after[k][3][i])<=2 for k in before for i in (0,1)),(before,after)
        return after
    command(['qs','ipc','-p',str(base/'config/quickshell'),'call','shell','panel',''])
    initial=windows();assert len(initial)>=3,'Open the applications preview first'
    first=initial[0]['id'];action('focus-window','--id',first)
    before=snap();toggle();wait(lambda:all(w['is_floating'] for w in windows()))
    # The same helper used by mouse grips must resize a real floating client.
    from floating_resize import resize
    window=next(w for w in windows() if w['id']==first)
    with patch.dict(os.environ,env):
        resize(dict(id=first,pid=window['pid'],output='winit',width=360,height=400,right=None,bottom=None,final=True))
    wait(lambda:all(abs(actual-wanted)<=2 for actual,wanted in zip(next(w for w in windows() if w['id']==first)['layout']['window_size'],[360,400])))
    action('set-window-width','--id',first,'300')
    command(['qs','ipc','-p',str(base/'config/quickshell'),'call','shell','page','main'])
    time.sleep(.3)
    screenshot=base/'window-mode-floating.png'
    action('screenshot-screen','--path',screenshot)
    deadline=time.monotonic()+4
    from PIL import Image
    while True:
        try:
            with Image.open(screenshot) as image:image.verify()
            break
        except (OSError,SyntaxError):
            if time.monotonic()>deadline:raise RuntimeError('Screenshot was not saved')
            time.sleep(.05)
    command(['qs','ipc','-p',str(base/'config/quickshell'),'call','shell','panel',''])
    toggle();after=check(before)
    ordered=sorted(windows(),key=lambda w:w['layout']['pos_in_scrolling_layout'])
    second=ordered[1]['id'];action('focus-window','--id',second);action('consume-or-expel-window-left','--id',second);time.sleep(.3)
    before=snap();toggle();wait(lambda:all(w['is_floating'] for w in windows()));toggle();after=check(before)
    # Isolate one test window on a different workspace; toggling must leave it tiled.
    other=next(w['id'] for w in reversed(ordered) if w['id']!=first);action('move-window-to-workspace','--window-id',other,'--focus','false','2')
    action('focus-window','--id',first);time.sleep(.2)
    before=snap();toggle();wait(lambda:any(w['is_floating'] for w in windows()))
    assert not next(w for w in windows() if w['id']==other)['is_floating']
    toggle();after=check(before)
    result=dict(passed=True,columns=True,stack=True,resized_floating_restored=True,other_workspace_untouched=True,before=before,after=after)
    (base/'window-modes-result.json').write_text(json.dumps(result,indent=2))
    print('PASS: column order, stacked windows, sizes and workspace isolation')

if __name__=='__main__':run(sys.argv[1])
