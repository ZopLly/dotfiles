#!/usr/bin/env python3
"""Offline regression checks: installation/rollback and session ID mapping."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from niri_config import flatten
def run(args, env=None):
    return subprocess.run(args, cwd=ROOT, env=env, check=True, text=True, capture_output=True)

with tempfile.TemporaryDirectory(prefix='niri-check-') as temp:
    home = Path(temp)
    env = dict(os.environ, HOME=temp, XDG_CONFIG_HOME=str(home/'config'), XDG_STATE_HOME=str(home/'state'), XDG_CACHE_HOME=str(home/'cache'))
    config = home/'config'
    (config/'niri').mkdir(parents=True)
    (config/'niri/config.kdl').write_text('// original\n')
    (config/'niri/extra.txt').write_text('keep me')
    (config/'kitty').mkdir()
    (config/'kitty/kitty.conf').write_text('untouched')
    before = (config/'niri/config.kdl').read_bytes()
    run(['python3', 'scripts/install.py', '--stage-only'], env)
    assert not (config/'niri').is_symlink()
    assert (config/'niri/config.kdl').read_bytes() == before
    # The separate build may write state; the dry-run check below uses its own path.
    dry_env = dict(env, XDG_STATE_HOME=str(home/'dry-state'))
    run(['python3', 'scripts/install.py'], dry_env)
    assert not (home/'dry-state').exists(), 'dry run wrote files'
    run(['python3', 'scripts/install.py', '--apply'], env)
    assert (config/'kitty/kitty.conf').read_text() == 'untouched'
    assert not (config/'kitty').is_symlink()
    assert (config/'niri').is_symlink()
    assert (config/'niri/extra.txt').read_text() == 'keep me'
    run(['niri', 'validate', '-c', str(config/'niri/config.kdl')], env)
    release = (config/'niri').resolve().parent
    assert not (release/'assets/themes/current').readlink().is_absolute()
    for path in release.rglob('*'):
        if path.is_symlink():
            assert path.exists(), path
    mocks = home/'theme-mocks'
    mocks.mkdir()
    for command in ('awww', 'gsettings', 'notify-send', 'magick'):
        helper = mocks/command
        helper.write_text('#!/bin/sh\n' + ('echo "test: currently displaying: image: test"\n' if command == 'awww' else '') + 'exit 0\n')
        helper.chmod(0o755)
    helper = mocks/'pgrep'
    helper.write_text('#!/bin/sh\nexit 1\n')
    helper.chmod(0o755)
    mock_env = dict(env, PATH=str(mocks)+os.pathsep+env['PATH'])
    original = (release/'niri/config.kdl').read_bytes()
    expanded = flatten(release/'niri/config.kdl').encode()
    assert b'shell-start' in expanded
    assert (release/'niri/conf.d/binds.kdl').is_file()
    assert (release/'niri/runtime.sh').is_file()
    assert b'spawn-at-startup \"waybar\"' not in expanded
    assert b'runtime.sh' in expanded and b' lock' in expanded and b' theme' in expanded
    assert 'custom/preview' not in (release/'waybar/config.jsonc').read_text()
    assert '(defpoll' in (release/'eww/eww.yuck').read_text()
    for theme in ('catppuccin-mocha', 'gruvbox-dark', 'tokyo-night'):
        for asset in (ROOT/'assets/themes'/theme).iterdir():
            if asset.is_file():
                assert asset.read_bytes() == (release/'assets/themes'/theme/asset.name).read_bytes()
    run(['bash', str(release/'scripts/theme-switcher.sh'), 'gruvbox-dark'], mock_env)
    assert (release/'assets/themes/current').readlink() == Path('gruvbox-dark')
    assert (release/'niri/config.kdl').read_bytes() == original
    assert (release/'alacritty/theme.toml').resolve() == release/'assets/themes/gruvbox-dark/alacritty.toml'
    bad = subprocess.run(['bash', str(release/'scripts/theme-switcher.sh'), '../invalid'], env=mock_env, capture_output=True)
    assert bad.returncode != 0
    assert (release/'assets/themes/current').readlink() == Path('gruvbox-dark')
    print('PASS: theme selection with mocked services; main config unchanged')
    manifest = next((home/'state/dotfiles/backups').glob('*/manifest.json'))
    assert json.loads(manifest.read_text())[-1]['target'] == str(config/'niri')
    run(['python3', 'scripts/install.py', '--rollback', str(manifest), '--apply'], env)
    assert not (config/'niri').is_symlink()
    assert (config/'niri/config.kdl').read_text() == '// original\n'
    assert not (config/'waybar').exists()
    print('PASS: dry run, snapshot installation, config validation, rollback')
    # Inject a mid-installation filesystem failure and verify automatic restoration.
    fault_code = """
from pathlib import Path
import os, runpy, sys
original = Path.symlink_to
def faulty(self, target, *args, **kwargs):
    if self == Path(os.environ['XDG_CONFIG_HOME'])/'eww':
        raise OSError('simulated install failure')
    return original(self, target, *args, **kwargs)
Path.symlink_to = faulty
sys.argv = ['scripts/install.py', '--apply']
runpy.run_path('scripts/install.py', run_name='__main__')
"""
    failed = subprocess.run(['python3', '-c', fault_code], cwd=ROOT, env=env, capture_output=True)
    assert failed.returncode != 0
    assert (config/'niri/config.kdl').read_text() == '// original\n'
    assert not (config/'alacritty').exists()
    assert not (config/'waybar').exists()
    assert (config/'kitty/kitty.conf').read_text() == 'untouched'
    print('PASS: interrupted installation restores previously switched components')
    # Both installation choices must have exactly one desktop shell in autostart.
    run(['python3', 'scripts/install.py', '--shell', 'legacy', '--apply'], env)
    legacy = (config/'niri/config.kdl').read_text()
    assert 'spawn-at-startup "waybar"' in legacy
    assert 'spawn-at-startup "qs"' not in legacy
    newest = sorted((home/'state/dotfiles/backups').glob('*/manifest.json'))[-1]
    run(['python3', 'scripts/install.py', '--rollback', str(newest), '--apply'], env)
    assert (config/'niri/config.kdl').read_text() == '// original\n'
    print('PASS: legacy shell installation and rollback')



    binary = home/'bin'
    binary.mkdir()
    fake = binary/'niri'
    fake.write_text('''#!/usr/bin/env python3
import json,sys
if sys.argv[-1]=='workspaces':
 print(json.dumps([{'id':42,'idx':2,'name':None,'output':'eDP-1'}]))
elif sys.argv[-1]=='windows':
 print(json.dumps([{'app_id':'Alacritty','workspace_id':42,'layout':{'pos_in_scrolling_layout':[3,1]}}, {'app_id':'firefox','workspace_id':42,'layout':{'pos_in_scrolling_layout':None}}]))
else: sys.exit(1)
''')
    fake.chmod(0o755)
    env['PATH'] = str(binary)+os.pathsep+env['PATH']
    run(['bash', 'session/save-session.sh'], env)
    data=json.loads((home/'state/niri-session/session.json').read_text())
    assert data['version']==2
    assert data['windows'][0]['workspace']=='2', 'must map ID 42 to index 2'
    assert data['windows'][0]['column']==3, 'column indices are already one-based'
    assert data['windows'][1]['column'] is None
    print('PASS: session workspace mapping and floating-window representation')

for path in ROOT.rglob('*.sh'):
    run(['bash', '-n', str(path)])
print('PASS: shell syntax')
for theme in ('catppuccin-mocha', 'gruvbox-dark', 'tokyo-night', 'ancient-odyssey'):
    config=flatten(ROOT/'niri/config.kdl', theme)
    with tempfile.NamedTemporaryFile(suffix='.kdl', mode='w') as file:
        file.write(config); file.flush()
        run(['niri','validate','-c',file.name])
print('PASS: all four Niri themes')
