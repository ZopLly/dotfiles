#!/usr/bin/env python3
"""Small read-only /proc sampler; the UI owns its lifetime while the dashboard is open."""
import json,os,sys,time
from pathlib import Path
sys.dont_write_bytecode=True

class Sampler:
    def __init__(self,proc=Path('/proc')):self.proc=Path(proc);self.previous=None
    def sample(self):
        result=dict(cpu=None,memory=None,memory_used=None,memory_total=None,swap=None,uptime=None,load=None,cores=os.cpu_count())
        try:
            fields=(self.proc/'stat').read_text().splitlines()[0].split()
            if fields[0]!='cpu':raise ValueError('missing aggregate')
            values=[int(x) for x in fields[1:9]]
            if len(values)<5:raise ValueError('incomplete cpu sample')
            total=sum(values);idle=values[3]+values[4]
            if self.previous:
                dt=total-self.previous[0];di=idle-self.previous[1]
                if dt>0 and 0<=di<=dt:result['cpu']=round((dt-di)*100/dt,1)
            self.previous=(total,idle)
        except (OSError,ValueError,IndexError):self.previous=None
        try:
            memory={key:int(value.split()[0]) for key,value in (line.split(':',1) for line in (self.proc/'meminfo').read_text().splitlines())}
            total=memory['MemTotal'];available=memory.get('MemAvailable')
            if total>0 and available is not None:
                used=max(0,min(total,total-available));result.update(memory=round(used*100/total,1),memory_used=used*1024,memory_total=total*1024)
            swap=memory.get('SwapTotal',0)
            if swap>0 and 'SwapFree' in memory:result['swap']=round(max(0,min(swap,swap-memory['SwapFree']))*100/swap,1)
        except (OSError,ValueError,KeyError):pass
        try:result['uptime']=int(float((self.proc/'uptime').read_text().split()[0]))
        except (OSError,ValueError,IndexError):pass
        try:result['load']=float((self.proc/'loadavg').read_text().split()[0])
        except (OSError,ValueError,IndexError):pass
        return result

def main():
    sampler=Sampler()
    while True:
        print(json.dumps(sampler.sample()),flush=True)
        if '--once' in sys.argv:return
        time.sleep(2)
if __name__=='__main__':main()
