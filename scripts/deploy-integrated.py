#!/usr/bin/env python3
"""Build a separate release, validate, then switch config links with rollback."""
import argparse,datetime,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('shell_update',ROOT/'scripts/apply-shell-update.py');shell=importlib.util.module_from_spec(spec);spec.loader.exec_module(shell)
COMPONENTS=('niri','quickshell','alacritty','mako','fuzzel','gtklock')
IDLE_UNIT='systemd/user/swayidle.service'

def command(args):return subprocess.check_output(args,text=True,stderr=subprocess.PIPE,timeout=8)

def link(path,target):
    temp=path.with_name('.'+path.name+'-shell-switch')
    if temp.is_symlink():temp.unlink()
    temp.symlink_to(target);os.replace(temp,path)

def prepare(applications_only=False):
    home=Path.home();config=home/'.config';old=(config/'quickshell').resolve().parent
    links={name:os.readlink(config/name) for name in COMPONENTS}
    if any((config/name).resolve()!=old/name for name in COMPONENTS):raise RuntimeError('Компоненты находятся в разных снимках; обновление остановлено')
    # Preserve the previous unit target; existing desktop-specific drop-ins stay in place.
    links[IDLE_UNIT]=os.readlink(config/IDLE_UNIT)
    idle_active=subprocess.run(['systemctl','--user','is-active','--quiet','swayidle.service'],capture_output=True).returncode==0
    current=shell.ipc(old,'status')
    if current.get('edit'):raise RuntimeError('Закончите перемещение виджетов перед обновлением')
    candidate=home/'.local/state/dotfiles/releases'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-integrated')
    shutil.copytree(old,candidate,symlinks=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    if applications_only:
        shutil.copy2(ROOT/'quickshell/applications/service.py',candidate/'quickshell/applications/service.py')
    else:
        shutil.rmtree(candidate/'quickshell')
        shutil.copytree(ROOT/'quickshell',candidate/'quickshell',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        shutil.rmtree(candidate/'assets')
        shutil.copytree(ROOT/'assets',candidate/'assets',symlinks=False,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        active=candidate/'assets/themes/current'
        if active.is_dir():shutil.rmtree(active)
        elif active.is_symlink():active.unlink()
        shutil.copytree((old/'assets/themes/current').resolve(),candidate/'assets/themes/_installed-current',symlinks=False)
        active.symlink_to('_installed-current')
        shutil.copy2(ROOT/'gtklock/minimal.css',candidate/'gtklock/minimal.css')
        for relative in ('layout.xml','scripts/lock.sh','scripts/blur-background.sh','modules/notifications.c',
                         'modules/minimal.c','modules/layout.c','modules/keyboard.c','modules/build.sh',
                         'modules/window-v4.h','modules/spectrum.h','modules/build-notifications.sh'):
            destination=candidate/'gtklock'/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/'gtklock'/relative,destination)
        subprocess.run(['bash',str(candidate/'gtklock/modules/build.sh')],check=True)

        shutil.copy2(ROOT/IDLE_UNIT,candidate/IDLE_UNIT)
        shutil.copy2(ROOT/'quickshell/cava_stream.py',candidate/'quickshell/cava_stream.py')
        wallpaper=candidate/'scripts/wallpaper.sh'
        content=wallpaper.read_text()
        start=content.index('wallpaper=');end=content.index('\n[[ -n',start)
        content=content[:start]+'wallpaper=$(python3 "$root/quickshell/appearance/wallpaper_start.py")'+content[end:]
        wallpaper.write_text(content)
    # Retarget only this release's own references, never external user files.
    for path in candidate.rglob('*'):
        if path.is_file() and not path.is_symlink():
            try:text=path.read_text()
            except (UnicodeError,OSError):continue
            changed=text.replace(str(old),str(candidate)).replace(str(ROOT),str(candidate))
            if changed!=text:path.write_text(changed)
    profile=(candidate/'alacritty/alacritty.toml').read_text()
    profile=re.sub(r'\[general\]\s*\nimport\s*=\s*\[[^\]]*\]','[general]\nimport = '+json.dumps([str(candidate/'assets/themes/current/alacritty.toml'),str(candidate/'assets/themes/current/terminal-opacity.toml')]),profile,count=1)
    profile=re.sub(r'(?ms)^\[colors(?:\.[^\]]*)?\].*?(?=^\[|\Z)','',profile)
    for name in ('niri.toml','alacritty.toml'):(candidate/'alacritty'/name).write_text(profile)
    binds=candidate/'niri/config.d/80-binds.kdl';text=binds.read_text()
    changes={'Mod+Down  { focus-window-down; }':'Mod+Down  { focus-workspace-down; }','Mod+Up    { focus-window-up; }':'Mod+Up    { focus-workspace-up; }','Mod+Ctrl+Down  { move-window-down; }':'Mod+Ctrl+Down  { move-window-to-workspace-down; }','Mod+Ctrl+Up    { move-window-up; }':'Mod+Ctrl+Up    { move-window-to-workspace-up; }'}
    for before,after in changes.items():text=text.replace(before,after)
    qs=json.dumps(str(candidate/'quickshell'))
    lines=[]
    for line in text.splitlines():
        if re.match(r'\s*Super\+Alt\+V\s',line):continue
        if re.match(r'\s*Mod\+T\s',line):line='    Mod+T { spawn "alacritty" "--config-file" '+json.dumps(str(candidate/'alacritty/niri.toml'))+'; }'
        elif re.match(r'\s*Super\+Space\s',line):line='    Super+Space { spawn "qs" "ipc" "-p" '+qs+' "call" "applications" "menu"; }'
        elif re.match(r'\s*Mod\+Shift\+T\s',line):line='    Mod+Shift+T { spawn "qs" "ipc" "-p" '+qs+' "call" "applications" "act" "settings" "-"; }'
        elif re.match(r'\s*Mod\+C\s',line):line='    Mod+C { spawn "qs" "ipc" "-p" '+qs+' "call" "applications" "act" "launch" "chatgpt.desktop"; }'
        lines.append(line)
    text='\n'.join(lines)+'\n'
    text=text.replace('binds {','binds {\n    Super+Alt+V { spawn "qs" "ipc" "-p" '+qs+' "call" "applications" "act" "launch" "Happ.desktop"; }',1)
    binds.write_text(text)
    main=candidate/'niri/config.kdl'
    rule='window-rule { match title="^Настройки Niri"; open-floating true; }'
    if rule not in main.read_text():main.write_text(main.read_text()+'\n'+rule+'\n')
    state=home/'.local/state/niri-shell'
    marker=candidate/'.shell-release.json';marker.write_text(json.dumps(dict(schema=1,root=str(candidate),state=str(state))));marker.chmod(0o600)
    widgets=state/'widgets.json'
    manifest=dict(old=str(old),candidate=str(candidate),links=links,idle_active=idle_active,widgets_sha256=hashlib.sha256(widgets.read_bytes()).hexdigest() if widgets.exists() else None)
    (candidate/'.deployment.json').write_text(json.dumps(manifest,indent=2))
    subprocess.run(['niri','validate','-c',str(candidate/'niri/config.kdl')],check=True)
    print('Prepared:',candidate,flush=True)
    return candidate

def reload_idle(data):
    if IDLE_UNIT not in data['links']:return
    subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True,check=True)
    if data.get('idle_active'):
        subprocess.run(['systemctl','--user','restart','swayidle.service'],capture_output=True,check=True)

def rollback(candidate):
    data=json.loads((candidate/'.deployment.json').read_text());old=Path(data['old'])
    active=(Path.home()/'.config/quickshell').resolve().parent
    shell.stop(active)
    for name,target in data['links'].items():link(Path.home()/'.config'/name,target)
    reload_idle(data)
    shell.start(old)
    subprocess.run(['makoctl','reload'],capture_output=True)
    print('Restored:',old,flush=True)

def apply(candidate):
    data=json.loads((candidate/'.deployment.json').read_text());old=Path(data['old'])
    if any(os.readlink(Path.home()/'.config'/name)!=target for name,target in data['links'].items()):raise RuntimeError('Конфигурация изменилась после подготовки')
    subprocess.run(['niri','validate','-c',str(candidate/'niri/config.kdl')],check=True)
    shell.stop(old)
    try:
        for name in data['links']:link(Path.home()/'.config'/name,candidate/name)
        reload_idle(data)
        shell.start(candidate)
        apps=json.loads(command(['qs','ipc','-p',str(candidate/'quickshell'),'call','applications','status']))
        if apps['error'] or apps['entries']<1:raise RuntimeError('Служба приложений не готова: '+apps['error'])
        state=Path.home()/'.local/state/niri-shell/widgets.json'
        if data['widgets_sha256'] and hashlib.sha256(state.read_bytes()).hexdigest()!=data['widgets_sha256']:raise RuntimeError('Состояние виджетов изменилось')
        subprocess.run(['makoctl','reload'],capture_output=True,check=True)
        (candidate/'.verified.json').write_text(json.dumps(dict(shell=shell.ipc(candidate,'systemStatus'),applications=dict(entries=apps['entries'],groups=len(apps['groups']),error=apps['error'])),ensure_ascii=False,indent=2))
        (candidate/'.verified.json').chmod(0o600)
        print('Applied:',candidate,flush=True)
    except BaseException:
        rollback(candidate);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--applications-only',action='store_true');parser.add_argument('--apply',type=Path);parser.add_argument('--rollback',type=Path);args=parser.parse_args()
    if args.rollback:rollback(args.rollback)
    elif args.apply:apply(args.apply.resolve())
    else:prepare(args.applications_only)
