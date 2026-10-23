"""Local appearance assets, resolved only beneath the supplied desktop root."""
import hashlib
import json
from pathlib import Path

class Catalogue:
    def __init__(self, root):
        self.root = Path(root).resolve()
        data = json.loads(self.safe('assets/appearance/catalog.json').read_text())
        self.presets = {p['id']: p for p in json.loads(self.safe('assets/appearance/hyprstack/presets.json').read_text())}
        self._themes = list(data['legacy'])
        for p in self.presets.values():
            self._themes.append(dict(id='hyprstack:'+p['id'], label=p['name'], group='hyprstack',
                modes=list(p['modes']), accents=[dict(id=k, **v) for k,v in p['accents'].items()],
                adapted_modes=[k for k,v in p['modes'].items() if not v.get('original',True)]))
        self._images = data['wallpapers']
        if len({t['id'] for t in self._themes}) != len(self._themes):
            raise ValueError('Повторяющийся идентификатор темы')
        if len({w['id'] for w in self._images}) != len(self._images):
            raise ValueError('Повторяющийся идентификатор обоев')

    def safe(self, relative):
        path = (self.root/relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError('Путь материала находится вне каталога оформления')
        return path

    def themes(self):
        return [dict(t) for t in self._themes]

    def wallpapers(self):
        return [dict(w) for w in self._images]

    def theme(self, identifier):
        result = next((dict(t) for t in self._themes if t['id']==identifier),None)
        if result is None:
            raise ValueError('Неизвестная тема')
        if result['group']=='legacy':
            result['path']=self.safe(result['directory'])
        return result

    def wallpaper(self, identifier):
        result = next((dict(w) for w in self._images if w['id']==identifier),None)
        if result is None:
            raise ValueError('Неизвестные обои')
        result['path']=self.safe(result['file'])
        if hashlib.sha256(result['path'].read_bytes()).hexdigest()!=result['sha256']:
            raise ValueError('Файл обоев повреждён')
        return result

    def legacy_file(self, identifier, name):
        theme=self.theme(identifier)
        if theme['group']!='legacy':raise ValueError('Ожидалась прежняя тема')
        path=self.safe(theme['path']/name)
        if not path.is_file():raise ValueError('Файл прежней темы отсутствует')
        return path
