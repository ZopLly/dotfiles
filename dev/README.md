# Разработка

`tests/` — проверки исходников; в установленную конфигурацию не копируются.
`reports/` — сохранённые локальные отчёты, не добавляемые в Git.

Примеры безопасных проверок:

```sh
python3 dev/tests/check_cava.py
python3 dev/tests/check_niri_modules.py
python3 dev/tests/check_notification_palette.py
python3 dev/tests/check_install_safety.py
python3 dev/tests/check_portable_install.py
```

Проверка безопасности моделирует ошибки записи и прерывание установки.
Последняя проверка собирает исходники из другой папки, запускает `--check`,
устанавливает окружение в отдельный временный HOME и проверяет откат. Настоящая сессия при этом не переключается.
