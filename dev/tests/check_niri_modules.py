#!/usr/bin/env python3
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('niri_modules',ROOT/'scripts/niri_config.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def blocks(text,name):
    lines=text.splitlines(keepends=True);result=[];i=0
    while i<len(lines):
        if not re.match('^'+re.escape(name)+r'\b',lines[i]):i+=1;continue
        chunk=[];depth=0;opened=False
        while i<len(lines):
            line=lines[i];chunk.append(line);i+=1
            clean=re.sub(r'r#".*?"#|"(?:\\.|[^"\\])*"|//[^\n]*','',line)
            depth+=clean.count('{')-clean.count('}');opened=opened or '{' in clean
            if opened and depth==0:break
        result.append(''.join(chunk))
    return result

class NiriModulesTests(unittest.TestCase):
    def test_all_native_include_candidates_validate(self):
        for theme in m.THEMES:
            with tempfile.NamedTemporaryFile('w',suffix='.kdl') as f:
                f.write(m.flatten(ROOT/'niri/config.kdl',theme));f.flush()
                subprocess.run(['niri','validate','-c',f.name],check=True,capture_output=True)

    def test_cycle_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'cycle.kdl';p.write_text('include "cycle.kdl"\n')
            with self.assertRaises(ValueError):m.flatten(p)

    def test_portable_runtime_uses_same_shell_path_for_start_and_ipc(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'qs';p.write_text('#!/usr/bin/env python3\nimport sys,json\nprint(json.dumps(sys.argv[1:]))\n');p.chmod(0o755)
            env=dict(os.environ,PATH=temp+os.pathsep+os.environ['PATH'])
            for action,tail in (('shell-start',[]),('panel',['right'])):
                result=subprocess.check_output(['bash',str(ROOT/'niri/runtime.sh'),action]+tail,env=env,text=True)
                args=json.loads(result)
                self.assertIn(str(ROOT/'quickshell'),args)
                if action=='panel':self.assertEqual(args[-3:],['shell','panel','right'])

unittest.main()
