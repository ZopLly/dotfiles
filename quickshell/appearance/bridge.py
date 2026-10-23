#!/usr/bin/env python3
"""JSON-lines adapter for the appearance settings process."""
import json
import os
from pathlib import Path
import sys
import subprocess
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from appearance.service import AppearanceService

def main():
    root=Path(__file__).resolve().parents[2]
    state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'niri-shell'
    service=AppearanceService(root,state,os.environ.get('NIRI_SHELL_PREVIEW')=='1')
    def emit(value):print(json.dumps(value,ensure_ascii=False),flush=True)
    emit(dict(type='state',data=service.snapshot()))
    for line in sys.stdin:
        try:
            request=json.loads(line)
            action=request.get('action')
            if action=='select':emit(dict(type='state',data=service.select(request.get('fields',{}))))
            elif action=='restore':emit(dict(type='state',data=service.restore_backup()))
            elif action=='confirm-wallpaper':emit(dict(type='state',data=service.confirm_wallpaper()))
            elif action=='thumbnail':
                identifier=request['id']
                emit(dict(type='thumbnail',id=identifier,url=service.thumbnail(identifier)))
            elif action=='state':emit(dict(type='state',data=service.snapshot()))
            else:raise ValueError('Неизвестное действие оформления')
        except (OSError,ValueError,KeyError,RuntimeError,subprocess.SubprocessError) as exc:
            emit(dict(type='error',message=str(exc)))
if __name__=='__main__':main()
