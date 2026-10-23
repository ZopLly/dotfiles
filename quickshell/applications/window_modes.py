"""Per-workspace floating sessions with a recoverable tiling snapshot.

Only native windows originally tiled (or newly created tiled windows) are managed.
Existing floating dialogs and windows moved to another workspace are left alone.
"""
import json
import math
import os
from pathlib import Path
import tempfile
from preview_scope import require_session, session_enabled


def capture(windows, workspace):
    result=[]
    for window in windows:
        pos=window.get('layout',{}).get('pos_in_scrolling_layout')
        if window.get('workspace_id')!=workspace or window.get('is_floating') or not pos:continue
        result.append(dict(id=window['id'],pid=window.get('pid'),position=pos,size=window['layout']['window_size']))
    return sorted(result,key=lambda w:(w['position'],w['id']))


def survivors(saved, windows, workspace):
    live={w['id']:w for w in windows if w.get('workspace_id')==workspace}
    columns={}
    for item in sorted(saved,key=lambda w:(w['position'],w['id'])):
        if item['id'] in live and live[item['id']].get('pid')==item.get('pid'):
            columns.setdefault(item['position'][0],[]).append(item)
    return list(columns.values())


def last_focus(windows,workspace):
    candidates=[w for w in windows if w.get('workspace_id')==workspace]
    def rank(window):
        stamp=window.get('focus_timestamp') or {}
        return (bool(window.get('is_focused')),stamp.get('secs',0),stamp.get('nanos',0))
    return max(candidates,key=rank)['id'] if candidates else None


class WindowModes:
    def __init__(self,root,state_dir,preview,command):
        self.root=Path(root);self.state_dir=Path(state_dir);self.preview=preview;self.command=command
        self.path=self.state_dir/'window-modes.json'

    def guard(self):require_session(self.root,self.state_dir,self.preview)

    def read(self):
        if self.path.is_symlink():raise ValueError('Состояние режима окон не может быть ссылкой')
        if not self.path.exists():return {}
        data=json.loads(self.path.read_text())
        if not isinstance(data,dict) or data.get('schema')!=1 or not isinstance(data.get('workspaces'),dict):raise ValueError('Повреждено состояние режимов окон; исходная раскладка сохранена в файле')
        if data.get('session')!=os.environ.get('NIRI_SOCKET'):return {}
        def number(value):
            try:return type(value) in (int,float) and value>0 and math.isfinite(value)
            except OverflowError:return False
        for key,state in data['workspaces'].items():
            valid=(key.isdigit() and int(key)<2**64 and isinstance(state,dict)
                and state.get('phase') in ('entering','floating','restoring') and isinstance(state.get('windows'),list))
            if valid:
                for item in state['windows']:
                    valid=(isinstance(item,dict) and type(item.get('id')) is int and 0<=item['id']<2**64
                        and (item.get('pid') is None or type(item['pid']) is int and item['pid']>0)
                        and isinstance(item.get('position'),list) and len(item['position'])==2
                        and all(type(v) is int and v>0 for v in item['position'])
                        and isinstance(item.get('size'),list) and len(item['size'])==2 and all(number(v) for v in item['size']))
                    if not valid:break
            if not valid:raise ValueError('Повреждён снимок раскладки; восстановление остановлено без удаления файла')
        return data['workspaces']

    def save(self,states):
        self.guard();self.state_dir.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.window-modes-',dir=self.state_dir)
        try:
            with os.fdopen(fd,'w') as output:json.dump(dict(schema=1,session=os.environ['NIRI_SOCKET'],workspaces=states),output)
            os.replace(name,self.path)
        finally:
            if Path(name).exists():Path(name).unlink()

    def windows(self):return json.loads(self.command(['niri','msg','-j','windows']))

    def action(self,name,window=None,*args):
        command=['niri','msg','action',name,*map(str,args)]
        if window is not None:command+=['--id',str(window)]
        return self.command(command)

    def status(self):return {key:value['phase'] for key,value in self.read().items()}

    def reconcile(self,windows):
        states=self.read()
        if not states:return False
        self.guard();changed=False
        for key,state in states.items():
            if state['phase']=='restoring':continue
            workspace=int(key);known={w['id'] for w in state['windows']}
            additions=[w for w in capture(windows,workspace) if w['id'] not in known]
            if additions:
                offset=max((w['position'][0] for w in state['windows']),default=0)
                for index,item in enumerate(additions):item['position']=[offset+index+1,1]
                state['windows']+=additions
                self.save(states) # Save before moving a new window out of tiling.
            live={w['id']:w for w in windows if w.get('workspace_id')==workspace}
            for item in state['windows']:
                window=live.get(item['id'])
                if window and window.get('pid')==item.get('pid') and not window.get('is_floating'):
                    self.action('move-window-to-floating',item['id']);changed=True
            if state['phase']!='floating':state['phase']='floating';self.save(states)
        return changed

    def toggle(self,output):
        self.guard()
        spaces=json.loads(self.command(['niri','msg','-j','workspaces']))
        space=next((w for w in spaces if w.get('is_active') and (w.get('output')==output if output else w.get('is_focused'))),None)
        if space is None:raise ValueError('Не найден текущий рабочий стол этого экрана')
        workspace=space['id'];key=str(workspace);states=self.read();windows=self.windows()
        if key not in states:
            states[key]=dict(phase='entering',windows=capture(windows,workspace))
            self.save(states);self.reconcile(windows)
            return
        # Include windows opened immediately before pressing the mode button.
        if states[key]['phase']!='restoring':self.reconcile(windows);states=self.read();windows=self.windows()
        state=states[key];state['phase']='restoring';self.save(states)
        columns=survivors(state['windows'],windows,workspace)
        focused=last_focus(windows,workspace)
        # Normalize our own windows first, so retry after a partial restore is safe.
        for column in columns:
            for item in column:self.action('move-window-to-floating',item['id'])
        for index,column in enumerate(columns,1):
            for tile_index,item in enumerate(column):
                identifier=item['id']
                self.action('move-window-to-tiling',identifier)
                self.action('focus-window',identifier)
                self.action('move-column-to-index',None,index+(1 if tile_index else 0))
                if tile_index:self.action('consume-or-expel-window-left',identifier)
            self.action('focus-window',column[0]['id'])
            self.action('set-column-width',None,str(column[0]['size'][0]))
            for item in column[:-1]:self.action('set-window-height',item['id'],str(item['size'][1]))
        if focused is not None and any(w['id']==focused for w in self.windows()):self.action('focus-window',focused)
        # Retain the snapshot until every native operation has succeeded.
        del states[key];self.save(states)
