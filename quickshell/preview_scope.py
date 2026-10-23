"""Fail closed before any side effect outside a disposable nested compositor."""
import json
import os
from pathlib import Path
import stat
import tempfile


def require_preview(root, state_dir, enabled):
    root=Path(root).resolve();state_dir=Path(state_dir).resolve()
    marker=root.parent/'.appearance-preview.json'
    try:
        data=json.loads(marker.read_text())
        runtime=Path(os.environ['XDG_RUNTIME_DIR']).resolve()
        ipc=Path(os.environ['NIRI_SOCKET']).resolve()
        allowed=(enabled and os.environ.get('NIRI_SHELL_PREVIEW')=='1'
            and root.is_relative_to(Path(tempfile.gettempdir()).resolve())
            and data==dict(root=str(root),state=str(state_dir),runtime=str(runtime))
            and runtime==root.parent/'runtime'
            and state_dir==root.parent/'state/niri-shell'
            and ipc.is_relative_to(runtime) and stat.S_ISSOCK(ipc.stat().st_mode)
            and not marker.is_symlink() and marker.stat().st_uid==os.getuid())
    except (OSError,ValueError,KeyError):allowed=False
    if not allowed:
        raise PermissionError('Изменения разрешены только в изолированном предпросмотре. Рабочее окружение не затронуто.')


def require_session(root,state_dir,preview):
    if preview:return require_preview(root,state_dir,True)
    root=Path(root).resolve();state_dir=Path(state_dir).resolve();home=Path.home()
    marker=root/'.shell-release.json'
    try:
        runtime=Path(os.environ['XDG_RUNTIME_DIR']).resolve();ipc=Path(os.environ['NIRI_SOCKET']).resolve()
        data=json.loads(marker.read_text())
        allowed=(os.environ.get('NIRI_SHELL_PREVIEW')!='1'
            and root.is_relative_to(home/'.local/state/dotfiles/releases')
            and data==dict(schema=1,root=str(root),state=str(state_dir))
            and state_dir==home/'.local/state/niri-shell'
            and (home/'.config/niri').resolve()==root/'niri'
            and (home/'.config/quickshell').resolve()==root/'quickshell'
            and marker.stat().st_uid==os.getuid() and not marker.is_symlink()
            and runtime.stat().st_uid==os.getuid() and ipc.is_relative_to(runtime)
            and stat.S_ISSOCK(ipc.stat().st_mode) and ipc.stat().st_uid==os.getuid())
    except (OSError,ValueError,KeyError):allowed=False
    if not allowed:raise PermissionError('Изменения разрешены только активному установленному снимку или изолированному предпросмотру.')


def session_enabled(root,state_dir,preview):
    try:require_session(root,state_dir,preview);return True
    except PermissionError:return False
