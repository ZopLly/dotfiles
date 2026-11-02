"""Locally count changes of focused desktop application, without titles or paths."""
import json,os,re,tempfile
from pathlib import Path

IDENTIFIER=re.compile(r'^[A-Za-z0-9_+.-]{1,240}\.desktop$')
class Usage:
    def __init__(self,path):
        self.path=Path(path);self.counts={};self.current=None
        try:
            if self.path.is_symlink():return
            data=json.loads(self.path.read_text())
            if data.get('version')!=1 or not isinstance(data.get('counts'),dict):return
            self.counts={k:v for k,v in data['counts'].items() if IDENTIFIER.fullmatch(k) and type(v) is int and 0<v<=10**9}
        except (OSError,ValueError,TypeError,AttributeError):pass
    def observe(self,identifier):
        if not isinstance(identifier,str) or not IDENTIFIER.fullmatch(identifier) or '..' in identifier:
            self.current=None;return False
        if self.current==identifier:return False
        self.current=identifier;self.counts[identifier]=min(10**9,self.counts.get(identifier,0)+1)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if self.path.is_symlink():raise ValueError('Usage file cannot be a symlink')
        fd,tmp=tempfile.mkstemp(prefix='.usage-',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w') as f:json.dump({'version':1,'counts':self.counts},f)
            os.replace(tmp,self.path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        return True
