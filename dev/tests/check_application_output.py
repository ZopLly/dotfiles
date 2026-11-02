#!/usr/bin/env python3
"""A real Gio child must not inherit the panel's JSON output channel."""
from pathlib import Path
import json, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
    base=Path(folder);entry=base/'synthetic.desktop'
    entry.write_text('[Desktop Entry]\nType=Application\nName=Synthetic test\nExec=/usr/bin/printf unexpected-child-output\n')
    code='''
import sys
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1])
from gi.repository import GioUnix
from applications.service import ApplicationService
entry=GioUnix.DesktopAppInfo.new_from_filename(sys.argv[2])
base=Path(sys.argv[2]).parent
service=ApplicationService(base,base/'state',[dict(id='synthetic.desktop')],False)
with patch('applications.service.require_session'),patch.object(GioUnix.DesktopAppInfo,'new',return_value=entry):
    service.action('launch','synthetic.desktop')
print('{"type":"done"}',flush=True)
'''
    result=subprocess.run([sys.executable,'-c',code,str(ROOT/'quickshell'),str(entry)],text=True,capture_output=True,timeout=5,check=True)
    assert result.stdout=='{"type":"done"}\n',repr(result.stdout)
print('PASS: native Gio application output cannot corrupt the JSON channel')
