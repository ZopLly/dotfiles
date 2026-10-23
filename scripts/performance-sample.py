#!/usr/bin/env python3
"""Passive freeze sampling: process CPU, PSI, scheduler gaps; no control commands."""
import argparse
import collections
import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time


def proc(pid):
    text = Path('/proc',str(pid),'stat').read_text()
    fields = text[text.rfind(')')+2:].split()
    return {'ticks':int(fields[11])+int(fields[12]), 'rss_kib':int(fields[21])*os.sysconf('SC_PAGE_SIZE')//1024}


def pressure():
    result={}
    for kind in ('cpu','memory','io'):
        for line in Path('/proc/pressure',kind).read_text().splitlines():
            fields=line.split()
            result[kind+'_'+fields[0]]={k:float(v) for k,v in (field.split('=') for field in fields[1:])}
    return result


def discover():
    output=subprocess.check_output(['ps','-eo','pid=,ppid=,comm='],text=True)
    result={}
    rows=[line.split(None,2) for line in output.splitlines()]
    for pid,ppid,comm in rows:
        if comm in ('qs','quickshell','niri','power-profiles-','awww-daemon'):
            result[int(pid)]=comm
    shell_pids={int(pid) for pid,ppid,comm in rows if comm in ('qs','quickshell')}
    for pid,ppid,comm in rows:
        if int(ppid) in shell_pids and comm in ('python','python3'):
            args=Path('/proc',pid,'cmdline').read_bytes().split(b'\0')
            script=next((Path(arg.decode()).name for arg in args if arg.endswith(b'.py')),comm)
            result[int(pid)]=script
    return result


def benchmark(live):
    spec=importlib.util.spec_from_file_location('measured_backend',live/'quickshell/backend.py')
    backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend)
    rows=[]
    original=backend.run
    calls=[]
    def measured(args,timeout=3):
        started=time.perf_counter()
        try:return original(args,timeout)
        finally:calls.append({'program':args[0],'ms':round((time.perf_counter()-started)*1000,3)})
    backend.run=measured
    for label in ('cold-1','warm-1','cold-2','warm-2','cold-3','warm-3'):
        if label.startswith('cold'):backend.SYSTEM_CACHE_TIME=0
        calls.clear();started=time.perf_counter();backend.snapshot()
        rows.append({'mode':label,'ms':round((time.perf_counter()-started)*1000,3),'processes':len(calls),'programs':dict(collections.Counter(c['program'] for c in calls)),'command_ms':list(calls)})
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--interval',type=float,default=.2)
    parser.add_argument('--benchmark',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 1<=args.seconds<=300 or not .05<=args.interval<=5:
        raise ValueError('Unsupported sample interval/duration')
    live=(Path.home()/'.config/quickshell').resolve().parent
    watched=discover();ticks=os.sysconf('SC_CLK_TCK')
    metadata={'kind':'metadata','time':datetime.datetime.now().astimezone().isoformat(),'duration':args.seconds,'interval':args.interval,'watched':watched,'live':str(live)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    samples=0;gaps=[];cpu=collections.defaultdict(list);seen_children=set()
    with args.output.open('w') as stream:
        os.chmod(args.output,0o600)
        stream.write(json.dumps(metadata)+'\n');stream.flush()
        last_time=time.monotonic();previous={pid:proc(pid) for pid in watched}
        until=last_time+args.seconds
        while time.monotonic()<until:
            time.sleep(args.interval)
            now=time.monotonic();elapsed=now-last_time
            row={'kind':'sample','time':datetime.datetime.now().astimezone().isoformat(),'elapsed':round(elapsed,5),'processes':{},'psi':pressure()}
            if elapsed>max(.7,args.interval*2):gaps.append(row['time'])
            for pid,name in watched.items():
                try:
                    current=proc(pid);before=previous[pid]
                    usage=100*(current['ticks']-before['ticks'])/ticks/elapsed
                    row['processes'][str(pid)]={'name':name,'cpu_percent':round(usage,3),'rss_kib':current['rss_kib']}
                    cpu[name].append(usage);previous[pid]=current
                    if name=='backend.py':
                        for task in Path('/proc',str(pid),'task').iterdir():
                            try:seen_children.update(int(p) for p in (task/'children').read_text().split())
                            except OSError:pass
                except (OSError,KeyError):row['processes'][str(pid)]={'name':name,'exited':True}
            stream.write(json.dumps(row)+'\n');stream.flush();samples+=1;last_time=now
        summary={'kind':'summary','samples':samples,'scheduler_gaps':gaps,'backend_children_observed':len(seen_children),'cpu':{name:{'mean':round(sum(v)/len(v),3),'max':round(max(v),3)} for name,v in cpu.items()}}
        if args.benchmark:summary['snapshot_benchmark']=benchmark(live)
        stream.write(json.dumps(summary)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
