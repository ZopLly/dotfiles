"""Read original palette values; no processes, mutation, or GUI dependencies."""
import re
import tomllib

def rgb(value):
    if not isinstance(value,str) or not re.fullmatch(r'#?[0-9a-fA-F]{6}',value):
        raise ValueError('Некорректный цвет палитры')
    return '#'+value.lstrip('#').lower()

def resolve_palette(catalogue, palette_id, mode=None, accent_id=None):
    theme=catalogue.theme(palette_id)
    if theme['group']=='legacy':
        if mode is not None or accent_id is not None:
            raise ValueError('Прежняя тема не имеет вариантов или акцентов')
        text=catalogue.legacy_file(palette_id,'waybar.css').read_text()
        colors=dict(re.findall(r'@define-color\s+(\w+)\s+(#[\da-fA-F]{6})',text))
        terminal=tomllib.loads(catalogue.legacy_file(palette_id,'alacritty.toml').read_text())['colors']
        normal=terminal.get('normal',{})
        bright=terminal.get('bright',normal)
        names=['black','red','green','yellow','blue','magenta','cyan','white']
        return dict(id=palette_id,mode=None,accent_id=None,legacy_path=theme['path'],
            bg=colors['bg'],fg=colors['fg'],accent=colors['accent'],
            fg_dim=colors.get('fg_dim',colors['fg']),surface=colors.get('surface',colors['bg']),
            outline=colors.get('accent'),error=colors.get('power_color','#f38ba8'),
            ansi=[normal.get(k,colors['fg']) for k in names]+[bright.get(k,colors['fg']) for k in names])
    raw=catalogue.presets[palette_id.split(':',1)[1]]
    mode=mode or 'dark'
    if mode not in raw['modes']:
        raise ValueError('Неизвестный вариант темы')
    c=raw['modes'][mode]
    accent=c['accent']
    if accent_id is not None:
        if accent_id not in raw['accents']:
            raise ValueError('Неизвестный акцент')
        accent=raw['accents'][accent_id][mode]
    roles=c.get('roles',{})
    return dict(id=palette_id,mode=mode,accent_id=accent_id,bg=rgb(c['background']),
        fg=rgb(c['foreground']),accent=rgb(accent),fg_dim=rgb(c['foreground']),
        surface=rgb(roles.get('surfaceContainer',c['background'])),
        outline=rgb(roles.get('outline',c['foreground'])),
        error=rgb(c.get('error',c['foreground'])),ansi=[rgb(v) for v in c['ansi']])
