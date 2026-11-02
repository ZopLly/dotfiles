#!/usr/bin/env python3
"""Exercise all wallpaper formats, cache hits and lock fallback in a temp fixture."""
import os, pathlib, shutil, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as temp:
    root=pathlib.Path(temp);scripts=root/'gtklock/scripts';scripts.mkdir(parents=True)
    shutil.copy2(ROOT/'gtklock/scripts/blur-background.sh',scripts/'blur-background.sh')
    themes=root/'assets/themes';themes.mkdir(parents=True)
    binary=root/'bin';binary.mkdir();log=root/'magick.log'
    (binary/'magick').write_text('#!/usr/bin/env python3\nimport sys,os,json\nfrom pathlib import Path\nwith open(os.environ["TEST_LOG"],"a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\nPath(sys.argv[-1]).write_bytes(b"test-jpeg")\n')
    (binary/'magick').chmod(0o755)
    env=dict(os.environ,PATH=str(binary)+':'+os.environ['PATH'],XDG_CACHE_HOME=str(root/'cache'),TEST_LOG=str(log))
    for name,extension in [('ancient-odyssey','jpg'),('catppuccin-mocha','gif'),('gruvbox-dark','png'),('tokyo-night','jpeg')]:
        theme=themes/name;theme.mkdir();(theme/f'wallpaper.{extension}').write_bytes(('wallpaper-'+name).encode())
        current=themes/'current'
        if current.is_symlink():current.unlink()
        current.symlink_to(name)
        command=['bash',str(scripts/'blur-background.sh')]
        output=subprocess.check_output(command,env=env,text=True).strip()
        assert pathlib.Path(output).read_bytes()==b'test-jpeg'
        before=log.read_text();subprocess.run(command,env=env,check=True,stdout=subprocess.DEVNULL)
        assert log.read_text()==before,'cache miss without wallpaper change'
        assert f'wallpaper.{extension}[0]' in before
        (theme/f'wallpaper.{extension}').write_bytes(('changed-'+name).encode())
        subprocess.run(command,env=env,check=True,stdout=subprocess.DEVNULL)
        assert log.read_text()!=before,'changed wallpaper did not invalidate cache'
    print('PASS: all four formats, GIF first frame, unchanged cache, changed-wallpaper invalidation')
