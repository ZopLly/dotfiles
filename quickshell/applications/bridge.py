#!/usr/bin/env python3
"""JSON-lines requests plus coalesced Niri window/workspace events."""
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import threading
import time
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from applications.model import desktop_entries
from applications.service import ApplicationService


def main():
    root=Path(__file__).resolve().parents[2]
    state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'niri-shell'
    catalogue=root.parent/'applications-catalogue.json'
    entries=json.loads(catalogue.read_text()) if os.environ.get('NIRI_SHELL_PREVIEW')=='1' and catalogue.is_file() else desktop_entries()
    service=ApplicationService(root,state,entries,preview=os.environ.get('NIRI_SHELL_PREVIEW')=='1')
    requests=queue.Queue();dirty=threading.Event();stopped=threading.Event();stream=[None]
    def emit(value):print(json.dumps(value,ensure_ascii=False),flush=True)
    def inputs():
        for line in sys.stdin:requests.put(line)
        requests.put(None)
    def events():
        while not stopped.is_set():
            try:
                process=subprocess.Popen(['niri','msg','-j','event-stream'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
                stream[0]=process
                for line in process.stdout:
                    if stopped.is_set():break
                    data=json.loads(line)
                    if any(key.startswith(('Window','Workspace')) for key in data):dirty.set()
                process.stdout.close();process.wait(timeout=2)
            except (OSError,ValueError,subprocess.SubprocessError):dirty.set()
            if not stopped.wait(1):dirty.set()
    def stop(*_):stopped.set();requests.put(None)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    threading.Thread(target=inputs,daemon=True).start()
    threading.Thread(target=events,daemon=True).start()
    emit(dict(type='catalogue',data=entries))
    previous=None;last=0;dirty.set()
    try:
        while not stopped.is_set():
            try:
                line=requests.get(timeout=.15)
                if line is None:break
                request=json.loads(line)
                if request.get('action')!='refresh':service.action(request.get('action'),request.get('value'))
                dirty.set();emit(dict(type='done'))
            except queue.Empty:pass
            except (OSError,ValueError,KeyError,RuntimeError,subprocess.SubprocessError) as exc:
                emit(dict(type='error',message=str(exc)));dirty.set()
            now=time.monotonic()
            if (dirty.is_set() and now-last>=.15) or now-last>=30:
                dirty.clear();last=now
                try:
                    data=service.snapshot()
                    if data!=previous:emit(dict(type='state',data=data));previous=data
                except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
                    emit(dict(type='error',message='Не удалось обновить окна: '+str(exc)))
    finally:
        stopped.set()
        if stream[0] and stream[0].poll() is None:stream[0].terminate()
        service.close()

if __name__=='__main__':main()
