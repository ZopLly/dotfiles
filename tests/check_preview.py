#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import re
import subprocess
import tempfile
import sys
sys.dont_write_bytecode = True

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('preview', root/'scripts/preview.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)
with tempfile.TemporaryDirectory(prefix='niri-preview-test-') as directory:
    base = Path(directory)
    config = preview.prepare(base)
    wallpaper = Path((base/'wallpaper-path').read_text())
    assert wallpaper.parent == config/'assets/themes/current'
    assert wallpaper.is_file()
    assert not any(p.is_symlink() for p in config.rglob('*'))
    niri = (config/'niri/config.kdl').read_text()
    active = '\n'.join(line for line in niri.splitlines() if not line.lstrip().startswith('//'))
    assert not re.search(r'^spawn(?:-sh)?-at-startup', active, re.M)
    for command in ('systemctl', 'brightnessctl', 'wpctl', 'playerctl', 'lock.sh', 'theme-switcher', 'firefox', 'orca'):
        assert command not in '\n'.join(line for line in active.splitlines() if 'spawn' in line), command
    assert 'mod-key-nested "Alt"' in active
    eww = (config/'eww/eww.yuck').read_text()
    assert '(defpoll' not in eww
    for command in re.findall(r':(?:onclick|onchange)\s+"([^"]*)"', eww):
        assert command == 'true' or command.startswith('eww '), command
    assert '<servicedir>' not in (base/'dbus.conf').read_text()
    for name in ('waybar/config.jsonc', 'eww/eww.yuck', 'niri/config.kdl', 'alacritty/alacritty.toml'):
        assert str(root) not in (config/name).read_text(), name
    subprocess.run(['niri', 'validate', '-c', str(config/'niri/config.kdl')], check=True)
print('PASS: isolated copies, disabled system actions/polls, private D-Bus, valid nested Niri config')
