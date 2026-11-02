# Новая оболочка: первая рабочая версия

Историческое описание первой версии. Сейчас Quickshell уже используется в рабочей сессии; актуальные входные точки описаны в README.md и PROJECT-STRUCTURE.md.

## Что сделано

- Слева: запуск Fuzzel, рабочие пространства текущего монитора, раскладка и название
  активного окна при достаточной ширине. Нажатие на раскладку переключает язык.
- Центр: островок времени расширяется в календарь и плеер. Календарь листается
  по месяцам и возвращается на текущую дату. Плеер работает через MPRIS: Spotify,
  браузеры и другие совместимые приложения, обложка, выбор плеера, пауза,
  предыдущий/следующий трек и перемотка при поддержке самим плеером.
- CAVA отображается в открытой медиапанели во время воспроизведения; в закрытой
  панели процесс визуализатора не работает.
- Справа: трей, Wi-Fi, Bluetooth, VPN-профили NetworkManager, звук, яркость,
  «не беспокоить», питание, доступные профили энергопотребления. Настройки устройств
  открываются в pavucontrol/nm-connection-editor/blueman-manager. Выключение,
  перезапуск и сон требуют подтверждения в панели.
- Под окнами: часы и медиакарточка. Свободное перемещение и изменение размеров в
  режиме редактирования. Привязку к сетке можно отключить. Набор и расположение хранятся
  отдельно для каждого экрана и рабочего пространства в `$XDG_STATE_HOME/niri-shell/widgets.json`
  (по умолчанию `~/.local/state/niri-shell/widgets.json`).
- Fuzzel: 62 символа ширины, 12 строк, иконки, увеличенные отступы и скругления.
  Цвета импортируются из существующей текущей темы.
- Ошибки системных команд показываются в панели, а не маскируются под успех.

## Цвета и ограничения первой версии

Все существующие файлы палитр и обои сохранены. Новая панель читает цвета Waybar
из assets/themes/current/waybar.css; Fuzzel использует прежние цвета Fuzzel.

Конструктор произвольных модулей центральной и правой шторок — следующий этап.
Сейчас каталог виджетов рабочего стола содержит часы и плеер. Каждый можно
включить или скрыть отдельно для текущего рабочего пространства. Виджеты локскрина,
погода, события внешнего календаря и история уведомлений пока не добавлены.
VPN-кнопки управляют только профилями NetworkManager. Они не обозначают состояние
Happ/Tailscale; отдельную интеграцию выбранного VPN-клиента нужно согласовать.
Нет активного плеера — показывается соответствующий текст, кнопки отключены.

## Предпросмотр

```sh
cd ~/dotfiles/niri-staging
./preview.sh
```

Островки раскрываются кликом. Правая шторка → «Расположение виджетов» → перетащи
карточку или её нижний правый угол. Нажми «Готово» в центральном островке или Esc.
В обычном режиме случайные клики не перемещают карточки.

В предпросмотре Alt заменяет Super. Alt+E открывает правую панель,
Alt+Shift+M — центральную, Alt+Space — Fuzzel. Alt+Shift+E завершает тестовый Niri.

Предпросмотр использует отдельную D-Bus-шину: текущий Spotify основной сессии там
не виден. При `--smoke` запускается тестовый плеер. Системные действия отключены;
Fuzzel показывает настоящие приложения с иконками, но не запускает выбранное.
Расположение виджетов сохраняется во временном профиле предпросмотра; каждый
новый запуск создаёт новый профиль. В установленной версии положение сохраняется
между входами в сессию.

## Установка после одобрения

```sh
./install.sh                    # план, без изменений
./install.sh --stage-only       # собрать копию, не подключая её
./install.sh --apply            # переключить на новую версию
```

После применения выйти из сессии и войти снова. До этого старые фоновые процессы
могут оставаться запущенными. Флаг `--session` для отдельного тестирования запрещён.

Для предыдущей оболочки в новой установочной копии:

```sh
./install.sh --shell legacy --apply
```

Для точного возврата к состоянию до установки — rollback по manifest.json,
который печатает установщик. Проверка установки выполнялась только во временных
каталогах; реальные конфиги новой версией пока не заменялись.

## Проверки

```sh
python3 dev/tests/check_cava.py
python3 dev/tests/check_shell.py
python3 dev/tests/check_preview.py
python3 dev/tests/check_staging.py
./preview.sh --smoke
```

Проверены загрузка Quickshell, обе панели и Fuzzel без ошибок конфигурации,
обнаружение тестового MPRIS-плеера и передача ему Pause/Next, сохранение координат
и размеров, ограничения значений, запрет системных действий в предпросмотре,
установка обеих оболочек, откат и восстановление после сбоя, завершение дочернего
процесса CAVA и очистка его временных файлов.
Реальные Wi-Fi, Bluetooth, VPN, питание и блокировка в ходе тестов не переключались.

## Виджеты по рабочим пространствам

Правая шторка → «Виджеты · пространство …» → «Часы» / «Плеер».
Подсвеченная кнопка означает, что виджет включён на текущем пространстве.
Скрытие сохраняет его положение и размер. Для перемещения включи
«Расположение виджетов», затем нажми «Готово».

Старое общее расположение переносится на пространство №1. Остальные изначально
пустые. Для безымянных пространств настройки привязаны к номеру: при перестановке
пространств набор остаётся у номера. Для именованных используется имя.
Это позволяет сохранять раскладку после перезапуска, не полагаясь на временные ID Niri.

## Session restore (prepared in staging)

At Niri login, a saved session opens a Fuzzel prompt: **Restore previous session**
or **Start fresh**. Escape dismisses the prompt without restoring apps. No prompt
appears when there is no saved session. Start fresh backs up the previous snapshot
as `~/.local/state/niri-session/previous-session.json`.

The new session manager automatically records Firefox, Alacritty and Spotify,
including workspace and monitor assignments and whether windows float. It saves
only after the supported-window layout has stayed unchanged for 15 seconds
(checked every 3 seconds). The last nonempty layout survives closing all windows.
It pauses saving on logind's shutdown signal and resumes if shutdown is cancelled.
This is a last-stable-layout snapshot: very recent changes may not be saved.

Restoration uses existing matching windows before launching new ones. Missing
monitors fall back to the current monitor. Exact column positions, window sizes,
terminal commands, working directories and unsaved documents are not restored.
Firefox tabs require Firefox's own “Open previous windows and tabs” setting;
this configuration does not change browser preferences. Spotify restores its own
account state. The supported executables must be installed normally on PATH.
The legacy shell and isolated preview do not start the session manager.

Checks: `python3 dev/tests/check_session.py` tests app filtering, workspace mapping,
private atomic storage, reuse/launch of windows, and shutdown/cancellation signals
with mocks. No real applications are launched by these tests.

## Panel module picker

Open the center or right island and click **Настроить модули**. Use **↑ / ↓**
to reorder, **−** to remove, and **+** to add a module. **Готово** returns to the
panel. Changes save automatically; **Вернуть стандартный набор** resets only the
panel being edited. Even an empty panel keeps the settings button.

Both panels accept calendar, player, connectivity (Wi-Fi/Bluetooth/DND), VPN,
audio, brightness, power, and desktop-widget controls. A module may appear once
in each panel. The tray stays at the top of the right panel. Existing palettes,
wallpapers and per-workspace desktop-widget positions are retained.

Panel choices are global across monitors/workspaces and persist in the `_panels`
section of `~/.local/state/niri-shell/widgets.json`. Desktop widgets remain scoped
to their own workspace. Preview settings stay in the temporary preview profile.
Unknown, duplicate or malformed module lists are rejected; damaged saved panel
lists fall back to defaults. This is a catalog of built-in modules, not a loader
for arbitrary third-party QML code.

Validation includes backend persistence, independent panel settings, empty
panels, invalid input, and an isolated graphical preview of both editors and
custom layouts. Preview hardware controls remain disabled.

Panel sizing: the curtain stays anchored at the top island. Its height follows
natural content height, capped at screen height minus 24 pixels. Overflow scrolls
vertically without stretching modules. Opening a panel or switching to its editor
resets scrolling to the top; shrinking content clamps the scroll position.

## Lock request coordination

The lock wrapper serializes manual/idle/sleep requests and skips launching a
second gtklock process for the same user. All managed callers use daemon mode,
so swayidle waits for lock acquisition instead of waiting until the user unlocks.
The launch mutex is not inherited by the daemon. Blurring is done at login with
an atomic cache replacement; locking uses the cache or the original lock wallpaper
immediately. No password/PAM configuration changes are made.

`python3 dev/tests/check_lock.py` uses fake commands to check concurrent requests,
background selection and error propagation without locking the desktop.
Real lock/unlock and suspend/resume require a user check after installation and
logging in again (the running swayidle service still uses the previous release).

## Moscow weather

Add **Погода** from either panel picker. Desktop: **Виджеты рабочего стола →
Погода**, then use the existing move/resize mode. It starts disabled to preserve
your layout. The desktop card is compact; the panel card expands a three-day
forecast. Moscow coordinates are fixed at 55.7558, 37.6173; units are Celsius and
dates use Europe/Moscow. No location detection or API key is needed.

Data source and API: https://open-meteo.com/en/docs (CC BY 4.0 attribution is
shown on the card). A separate process refreshes every 15 minutes, with a
10-second network timeout and five-minute retries. Last successful data lives in
`$XDG_CACHE_HOME/niri-shell/weather-moscow.json`; offline readings are marked and
dated. Preview uses clearly labelled sample weather and makes no API requests.
Tests: `python3 dev/tests/check_weather.py`; live Moscow response parsing was also
checked without changing the active configuration.

## Google Calendar events (read-only)

Click a date to show its agenda. Dots mark dates with loaded events. The feed
refreshes every ten minutes, covering the previous 31 days and next 183 days.
Times are displayed in Europe/Moscow. Recurrence, exclusions, cancelled events,
and multi-day spans are processed by icalendar + recurring-ical-events. A failed
refresh keeps the current in-memory agenda with a visible error; event data is
not cached to disk. The preview shows labelled sample events and never reads the
private URL.

After approving installation:

1. Install the optional libraries in an isolated user environment:
   `bash ~/dotfiles/niri-staging/scripts/setup-calendar.sh`
2. In Google Calendar: Settings → Settings for my calendars → choose calendar →
   Integrate calendar → **Secret address in iCal format**.
   Google instructions: https://support.google.com/calendar/answer/37648?hl=en
3. Create the local file (outside either Git repository):

   ```sh
   mkdir -p ~/.config/niri-shell
   touch ~/.config/niri-shell/google-calendar.url
   chmod 600 ~/.config/niri-shell/google-calendar.url
   nano ~/.config/niri-shell/google-calendar.url
   ```

   Paste only the secret URL, save and close. Do not paste it into chat or commit
   it. The service uses `$XDG_CONFIG_HOME` when set; adjust the above path if needed.
4. Log in again after installation. This also starts the optional-library Python
   interpreter. The service can detect a newly added URL without another login
   if the libraries were already installed before it started.

Only HTTPS feeds under calendar.google.com/calendar/ical/ are accepted; redirects
are refused. Error messages never include request URLs. If the Secret address
option is absent on a managed Google account, an administrator may have disabled
it; account sign-in/OAuth would require a separate integration. No events can be
created or edited from this widget.

Tests: `/tmp/niri-calendar-test/bin/python dev/tests/check_calendar.py` in this
session; after setup use `~/.local/share/niri-shell/calendar-venv/bin/python
 dev/tests/check_calendar.py`. Dependencies are pinned in calendar-requirements.txt.
