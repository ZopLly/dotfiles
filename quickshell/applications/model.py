"""Pure window grouping; Gio metadata never carries executable shell text."""
from collections import defaultdict


def desktop_entries():
    import gi
    gi.require_version('Gio','2.0')
    gi.require_version('GioUnix','2.0')
    from gi.repository import Gio, GioUnix
    result={}
    for app in Gio.AppInfo.get_all():
        identifier=app.get_id()
        if not identifier or not app.should_show():continue
        icon=app.get_icon();name=''
        if isinstance(icon,Gio.ThemedIcon):name=next(iter(icon.get_names()),'')
        elif isinstance(icon,Gio.FileIcon):name=icon.get_file().get_uri()
        aliases=[identifier.removesuffix('.desktop')]
        startup=app.get_startup_wm_class() if isinstance(app,GioUnix.DesktopAppInfo) else None
        if startup:aliases.append(startup)
        result[identifier]=dict(id=identifier,name=app.get_display_name() or identifier,icon=name,aliases=aliases)
    return sorted(result.values(),key=lambda app:(app['name'].casefold(),app['id']))


def groups(entries, windows, workspaces, current_only=False, output=None):
    exact={e['id'].removesuffix('.desktop'):e for e in entries}
    aliases=defaultdict(list)
    for entry in entries:
        for name in set(a.casefold() for a in [entry['id'].removesuffix('.desktop'),*entry['aliases']] if a):aliases[name].append(entry)
    spaces={w['id']:w for w in workspaces}
    active={w['id'] for w in workspaces if w.get('is_active') and (output is None or w.get('output')==output)}
    result={}
    for window in windows:
        if current_only and window.get('workspace_id') not in active:continue
        app_id=window.get('app_id') or ''
        key=app_id.removesuffix('.desktop').casefold()
        entry=exact.get(app_id.removesuffix('.desktop'))
        if entry is None and len(aliases[key])==1:entry=aliases[key][0]
        identifier=entry['id'] if entry else ('window-app:'+key if key else 'window:'+str(window['id']))
        if identifier not in result:
            result[identifier]=dict(id=identifier,desktop_id=entry['id'] if entry else None,
                name=entry['name'] if entry else (app_id or 'Окно'),icon=entry['icon'] if entry else '',
                active=False,urgent=False,windows=[])
        group=result[identifier];space=spaces.get(window.get('workspace_id'),{})
        group['active'] |= bool(window.get('is_focused'))
        group['urgent'] |= bool(window.get('is_urgent'))
        group['windows'].append(dict(window,workspace_label=str(space.get('name') or space.get('idx') or '—'),output=space.get('output')))
    # Stable app order: focusing a window must not move the pointer's target.
    for group in result.values():
        group['windows'].sort(key=lambda w:(not w.get('is_focused',False),w.get('workspace_id') or 0,w['id']))
    return sorted(result.values(),key=lambda g:(g['name'].casefold(),g['id']))
