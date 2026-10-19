# Minimal lock screen

Default: **Minimal**. Applied 2026-10-13 at 13:46 Europe/Moscow to the active
snapshot `~/.local/state/dotfiles/releases/20260918-120609-677912`.

## Implementation and security

The active locker remains **gtklock 4.0.0**, using `ext-session-lock-v1` and the
existing PAM service `/etc/pam.d/gtklock` (`auth include login`). No authentication
code, PAM files, system services, suspend policy, or notification exposure changed.
The layout retains gtklock's password activation, error/message widgets and native
handlers. Checking disables input and shows the native busy cursor; failure shows
`Login failed`; success releases the real session lock. Password reveal remains
an explicit entry-icon action, as before.

`Super+Alt+L`, Quickshell's lock action and swayidle invoke the same installed
`gtklock/scripts/lock.sh`. The active user service runs `swayidle -w`: lock after
650 seconds, suspend after 950, and the same lock command `before-sleep`.
The existing mutex and `gtklock --daemonize` readiness wait are retained; image
processing never happens in the before-sleep path. Wrapper failures propagate.
`swaylock/config` is a legacy fallback and is not used by these active launch paths.
No whole-session or service restart was performed.

## Appearance and themes

Large time, date, centered password entry, a small Unlock button, native errors,
and battery status near the bottom. No weather, controls or settings panels.
The media line is optional; a hidden line takes no layout space.

`assets/themes/current` is the existing source of truth. At each lock, the wrapper
selects its `gtklock.css` and wallpaper/cache. All four themes are supported:
Ancient Odyssey, Catppuccin Mocha, Gruvbox Dark and Tokyo Night. A theme switch
therefore affects the next lock, including the wallpaper, text, entry, border,
accent and overlay. A currently locked screen is intentionally not restyled.

`gtklock/minimal.css` holds the shared preset. Tiny theme CSS files are generated
by `scripts/lockscreen-tokens.py` from the existing Waybar palette and Niri active
outline. Secondary text is lightened only where needed for 4.5:1 contrast against
opaque theme surfaces; overlay alpha is derived from the theme background.
`gtklock/style.css` provides the Ancient Odyssey fallback. Its primary/secondary
text is #F3E7D0/#D9CCB8, surface #203447, outline #D8C6AA, accent #81B5D5.
After editing shared palettes, regenerate tokens and run `--check`.

## Wallpaper blur

The previous script assumed `wallpaper.jpg`, breaking other theme formats.
It now matches `scripts/wallpaper.sh` selection: PNG, JPG, JPEG, GIF or WebP from
the current theme; an animated source uses its first frame only.

The theme switcher/startup pre-generates
`$XDG_CACHE_HOME/gtklock-THEME.jpg` (default `~/.cache`), using a moderate static
12-pixel blur, slight darkening and a maximum 2560×1440 resolution. The wallpaper
hash plus preset version invalidates the cache. Unchanged images skip processing;
replacement is atomic. There is no live blur shader. If a cache is missing, lock
uses the original wallpaper immediately. Missing artwork falls back to the locker
background instead of preventing locking. The active Odyssey cache was regenerated.

## Media and battery

`gtklock/modules/minimal.c` is a small display-only GTK/GIO module loaded inside
gtklock; no Python daemon, subprocess polling, media service, or album-art downloads.
It asynchronously reads MPRIS players and subscribes to property/name changes.
A line appears **only for Playing with a valid, nonblank track title**; artist is
optional. Paused, Stopped, unavailable and invalid metadata hide it completely,
including after GTK show-all operations. Labels use plain text, truncate long
metadata, accept no keyboard focus, and offer no controls that interfere with typing.

Battery percentage and Charging/Full/On battery come from UPower DisplayDevice
properties and update through DBus signals. Missing battery data hides the label.
Each monitor gets its own labels; destroyed windows are removed from the view list.

Build: `bash gtklock/modules/build.sh`. Existing gcc, pkg-config, GTK3 and GIO were
sufficient; no packages were installed. The header ABI is pinned to upstream
[gtklock v4.0.0](https://github.com/jovanlanik/gtklock/tree/v4.0.0), commit
`66321fb2bf0d5869d779e7ac6b4d8d9c272ea707`; its license is retained alongside it.
The installer now builds the ignored `.so` before copying a snapshot and checks
build-tool availability. The wrapper loads this module only for gtklock 4.0.x;
on a future ABI change, authentication still works without the optional labels,
but the module must be reviewed/rebuilt. No install-on-lock behavior exists.

## Changed files

- `gtklock/config.ini`, `layout.xml`, `style.css`, new `minimal.css`.
- `gtklock/scripts/{lock,blur-background}.sh`.
- `gtklock/modules/{minimal.c,window-v4.h,build.sh,GTKLOCK-LICENSE}`;
  locally built `minimal-module.so` is not tracked.
- `assets/themes/{ancient-odyssey,catppuccin-mocha,gruvbox-dark,tokyo-night}/gtklock.css`.
- `scripts/{lockscreen-tokens,apply-lockscreen-minimal}.py`, build step in `install.py`.
- `.gitignore`, lock/blur/GTK tests and this guide. No commit or push performed.

## Verification and safe manual test

Completed:

1. C module builds with `-Wall -Wextra -Werror`; shell syntax and Python compilation pass.
2. `tests/check_lock.py`: serialized requests, readiness flags, no inherited mutex,
   cached/fallback background and propagation of locker failure.
3. `tests/check_lock_blur.py`: four wallpaper formats, GIF first frame, cache hit
   and invalidation when wallpaper changes, in isolated temporary directories.
4. GTK/Xvfb test `tests/lockscreen-ui.c`: valid Playing, Paused/Stopped/no player,
   blank/malformed metadata, hidden widget visibility, required layout IDs and
   parsing all four theme CSS. Offscreen screenshots inspected with/without music.
5. `python3 tests/preview_lock_minimal.py`: **real gtklock process** acquired the
   session lock in a disposable nested Niri, loading the custom XML and module.
   Nested Niri logs confirmed `locking session`. Parent desktop was not locked.
6. `niri validate -c /home/andrew/dotfiles/niri-staging/niri/config.kdl`: passed.
   All 11 deployed file hashes match the payload; generated blur is a valid JPEG.

Not yet physically tested: actual password success/failure, suspend/resume,
charging cable transitions, monitor hotplug and a four-theme switch cycle in the
real session. The isolated test did **not** bypass or exercise PAM authentication.
The full installer was not run during preparation.

For first manual verification, save work and use **Super+Alt+L**. Enter one wrong
password and then the correct password locally. Test Playing → Paused → Playing
from another trusted device/app control if available, then suspend/resume after
successful unlock verification. Do not enter passwords into chat or test scripts.
Switch themes using the normal switcher and lock again to verify each appearance.
If lock is already active, unlock before applying or rolling back files.

## Rollback

Backup:
`~/.local/state/dotfiles/lockscreen-backups/20261013-134646-629700`.

From staging:

```sh
python3 scripts/apply-lockscreen-minimal.py --rollback /home/andrew/.local/state/dotfiles/lockscreen-backups/20261013-134646-629700 --apply
```

This restores the previous locker files, theme CSS and cached background; it
removes only files introduced by this deployment and rejects later file edits.
It neither starts a lock nor restarts a session/service. The old configuration
remains in the backup; widget settings and all Quickshell files are untouched.
