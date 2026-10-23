#!/usr/bin/env python3
"""Assemble repository modules; retain leaf theme includes for native Niri merging."""
import argparse
import json
from pathlib import Path
import re

INCLUDE = re.compile(r'^\s*include\s+("(?:\\.|[^"\\])*")\s*(?://.*)?$')
THEMES = ('catppuccin-mocha','gruvbox-dark','tokyo-night','ancient-odyssey')


def flatten(path, theme=None, stack=()):
    path=Path(path).resolve()
    if path in stack or len(stack)>=32:
        raise ValueError('Recursive/deep Niri include: '+str(path))
    lines=[]
    for line in path.read_text().splitlines():
        match=INCLUDE.match(line)
        if not match:
            lines.append(line);continue
        target=Path(json.loads(match[1])).expanduser()
        if not target.is_absolute():target=path.parent/target
        if theme and target.name=='niri-runtime.kdl' and target.parent.name=='current':
            if theme not in THEMES:raise ValueError('Unknown theme')
            target=target.parent.parent/theme/target.name
        if target.name == 'niri-runtime.kdl':
            # Duplicate layout blocks are illegal within one file. Niri merges
            # separately parsed includes, so this leaf must remain an include.
            lines.append('include '+json.dumps(str(target.resolve())))
        else:
            lines.append('// Included: '+target.name)
            lines.append(flatten(target,theme,stack+(path,)))
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config',type=Path)
    parser.add_argument('--theme',choices=THEMES)
    args=parser.parse_args()
    print(flatten(args.config,args.theme),end='')
