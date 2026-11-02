"""Generate consumer files in memory; callers decide where and whether to write."""
import json
from .palette import resolve_palette

def render_theme(catalogue,selection):
    p=resolve_palette(catalogue,selection['palette_id'],selection['mode'],selection['accent_id'])
    if 'legacy_path' in p:
        files={name:catalogue.legacy_file(selection['palette_id'],name).read_bytes() for name in
            ('waybar.css','alacritty.toml','fuzzel.ini','mako.conf','gtklock.css','niri-runtime.kdl','eww.scss')}
        files['gtklock.css']=files['gtklock.css'].replace(b'../../../gtklock/minimal.css',str(catalogue.root/'gtklock/minimal.css').encode())
        files['mako.conf']=('background-color='+p['bg']+'\ntext-color='+p['fg']+'\nborder-color='+p['accent']+'\nprogress-color=over '+p['surface']+'\n[urgency=critical]\nborder-color='+p['error']+'\n').encode()
        files['palette.json']=json.dumps({k:v for k,v in p.items() if k!='legacy_path'}).encode()
        return files
    bg,fg,accent,surface,outline,error=(p[k] for k in ('bg','fg','accent','surface','outline','error'))
    tokens=dict(bg=bg,fg=fg,fg_dim=fg,bg_modules=bg,surface=surface,hover=surface,
                accent=accent,cava_color=accent,clock_color=fg,power_color=error)
    css=''.join('@define-color '+k+' '+v+';\n' for k,v in tokens.items())
    css+='@define-color shell_bg_modules rgba('+', '.join(str(int(bg[i:i+2],16)) for i in (1,3,5))+', 0.95);\n'
    names=['black','red','green','yellow','blue','magenta','cyan','white']
    term='[colors.primary]\nbackground = "'+bg+'"\nforeground = "'+fg+'"\n'
    term+='[colors.cursor]\ntext = "'+bg+'"\ncursor = "'+accent+'"\n'
    term+='[colors.selection]\ntext = "'+fg+'"\nbackground = "'+surface+'"\n'
    for kind,offset in [('normal',0),('bright',8)]:
        term+='[colors.'+kind+']\n'+''.join(n+' = "'+p['ansi'][offset+i]+'"\n' for i,n in enumerate(names))
    fuzzel='[colors]\n'+''.join(k+'='+v.lstrip('#')+'ff\n' for k,v in
        [('background',bg),('text',fg),('match',accent),('selection',surface),('selection-text',fg),('border',accent)])
    mako='background-color='+bg+'\ntext-color='+fg+'\nborder-color='+accent+'\nprogress-color=over '+surface+'\n[urgency=critical]\nborder-color='+error+'\n'
    lock=''.join('@define-color lock_'+k+' '+v+';\n' for k,v in
        [('fg',fg),('dim',fg),('bg',bg),('surface',surface),('accent',accent),('border',outline),('error',error)])
    lock+='@define-color lock_overlay rgba(0,0,0,0.22);\n@import url("'+str(catalogue.root/'gtklock/minimal.css')+'");\n'
    niri='layout {\n    focus-ring { active-color "'+accent+'"; inactive-color "'+outline+'"; }\n    border { off; active-color "'+accent+'"; inactive-color "'+outline+'"; }\n}\n'
    files={'waybar.css':css,'alacritty.toml':term,'fuzzel.ini':fuzzel,'mako.conf':mako,
           'gtklock.css':lock,'niri-runtime.kdl':niri,'eww.scss':''.join('$'+k+': '+v+';\n' for k,v in tokens.items()),
           'palette.json':json.dumps(p)}
    return {k:v.encode() for k,v in files.items()}
