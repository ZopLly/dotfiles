#!/usr/bin/env python3
"""Compare read-only snapshots and event refresh costs; never run control actions."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time

SCOPES={'cold':None,'warm':set(),'audio':{'audio_levels'},'brightness':{'brightness'},'power':{'power'},'network':{'wifi','vpns'},'niri':{'niri'}}


def measure(path):
    for name in ('system_state','state_cache'):
        sys.modules.pop(name,None)
    spec=importlib.util.spec_from_file_location('bench_'+str(abs(hash(path))),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original=module.run;calls=[]
    def tracked(args,timeout=3):
        calls.append(args[0]);return original(args,timeout)
    module.run=tracked;rows=[]
    for mode,scopes in SCOPES.items():
        for repeat in range(3):
            if hasattr(module,'CACHE'):
                module.CACHE.invalidate(scopes)
            elif mode not in ('warm','niri'):
                module.SYSTEM_CACHE_TIME=0
            calls.clear();started=time.perf_counter();module.snapshot()
            rows.append({'mode':mode,'repeat':repeat+1,'ms':round((time.perf_counter()-started)*1000,3),'processes':len(calls),'programs':list(calls)})
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    before=(Path.home()/'.config/quickshell/backend.py').resolve()
    result={'before_path':str(before),'after_path':str(root/'quickshell/backend.py'),'before':measure(before),'after':measure(root/'quickshell/backend.py')}
    args.output.write_text(json.dumps(result,indent=2))
    for mode in SCOPES:
        line=[mode]
        for side in ('before','after'):
            rows=[r for r in result[side] if r['mode']==mode]
            line.append(f"{side}: {sum(r['ms'] for r in rows)/len(rows):.2f} ms, {rows[0]['processes']} processes")
        print(' | '.join(line))

if __name__=='__main__':main()
