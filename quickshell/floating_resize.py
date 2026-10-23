#!/usr/bin/env python3
"""Resize only an identified floating window through Niri's local IPC socket."""
import json,math,os,queue,signal,socket,sys,threading,time
from pathlib import Path
from preview_scope import require_session

def rpc(request):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(2)
        connection.connect(os.environ['NIRI_SOCKET'])
        connection.sendall(json.dumps(request).encode()+b'\n')
        with connection.makefile('rb') as stream:response=json.loads(stream.readline(2**20))
    if 'Err' in response:raise ValueError(response['Err'])
    return response['Ok']

def resize(request,command=rpc):
    def number(key,low,high,optional=False):
        value=request.get(key)
        if optional and value is None:return None
        if type(value) not in (float,int) or not math.isfinite(value) or not low<=value<=high:raise ValueError('Недопустимый размер окна')
        return value
    width=round(number('width',120,16384));height=round(number('height',100,16384))
    right=number('right',-32768,32768,True);bottom=number('bottom',-32768,32768,True)
    identifier=request.get('id')
    if type(identifier) is not int or identifier<0:raise ValueError('Неизвестное окно')
    def window():
        found=next((w for w in command('Windows')['Windows'] if w['id']==identifier),None)
        if not found or not found['is_floating'] or found.get('pid')!=request.get('pid'):raise ValueError('Изменение размера доступно только свободному окну')
        spaces=command('Workspaces')['Workspaces']
        if not any(w['id']==found['workspace_id'] and w['is_active'] and w.get('output')==request.get('output') for w in spaces):raise ValueError('Рабочий стол окна изменился')
        return found
    found=window()
    command({'Action':{'SetWindowWidth':{'id':identifier,'change':{'SetFixed':width}}}})
    window() # A mode switch during the drag must stop subsequent mutations.
    command({'Action':{'SetWindowHeight':{'id':identifier,'change':{'SetFixed':height}}}})
    if right is not None or bottom is not None:
        if request.get('final'):time.sleep(.05)
        found=window();layout=found['layout'];pos=layout['tile_pos_in_workspace_view'];offset=layout['window_offset_in_tile']
        size=layout['window_size'] if request.get('final') else [width,height]
        dx=right-size[0]-pos[0]-offset[0] if right is not None else 0.
        dy=bottom-size[1]-pos[1]-offset[1] if bottom is not None else 0.
        command({'Action':{'MoveFloatingWindow':{'id':identifier,'x':{'AdjustFixed':float(dx)},'y':{'AdjustFixed':float(dy)}}}})

def main():
    root=Path(__file__).resolve().parent.parent
    state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'niri-shell'
    preview=os.environ.get('NIRI_SHELL_PREVIEW')=='1'
    requests=queue.Queue()
    def inputs():
        for line in sys.stdin:
            try:requests.put(json.loads(line))
            except ValueError:pass
        requests.put(None)
    threading.Thread(target=inputs,daemon=True).start()
    while True:
        request=requests.get()
        if request is None:return
        while not requests.empty():
            newer=requests.get()
            if newer is None:return
            request=newer
        try:
            require_session(root,state,preview)
            resize(request)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            print(json.dumps({'error':str(exc)},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
