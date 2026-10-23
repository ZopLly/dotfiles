# Niri appearance implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Prepare the agreed appearance catalogue and a working settings window in an isolated Niri preview.
**Architecture:** Keep the four existing themes read-only; vendor the 18 palette definitions and 11 original wallpapers. Small Python modules own catalogue, rendering, selection and preview activation; a separate Quickshell window uses a JSON-lines bridge.
**Tech Stack:** Python standard library, Pillow (existing), QtQuick Controls, Quickshell, Niri, awww.
**Spec:** ../specs/2026-10-22-niri-appearance-design.md
**Execution:** Inline, as requested by the user; continue without repeated design approval. Existing staging is the explicitly chosen isolated development location.

## Global Constraints
- Work only in /home/andrew/dotfiles/niri-staging; keep the existing 77 dirty paths untouched.
- Never apply to the installed environment or run installers/live theme switchers.
- Preserve all existing theme colors, wallpapers, widget state, and Hyprstack configuration.
- No SSH keys, new packages, publication, push or session restarts.
- Commit only this plan's files; test against temporary directories.

## Review Focus
- Relocation and traversal: resolved asset paths stay in the supplied project root, symlink escapes fail.
- Palette and wallpaper changes must never reset the other choice.
- Broken state or a failed external update must not be reported as successful.
- Preview isolation must be checked using actual paths and sockets, not only a boolean flag.
- Rendered light themes, terminal imports, and gtklock CSS paths must work outside the source theme directory.

### Task 1: Catalogue and palette data
**Files:** assets/appearance/**, assets/wallpapers/library/**, quickshell/appearance/{__init__,catalog,palette}.py, tests/check_appearance_catalog.py.
**Interfaces:** Catalogue(root: Path), .themes(), .wallpapers(), .theme(id), .wallpaper(id); resolve_palette(catalogue, palette_id, mode=None, accent_id=None) -> dict.
- [x] Write and run failing tests for a relocatable 22-theme/11-wallpaper catalogue, preserved hashes/animation, known original colors, accents, unknown IDs, and path escapes.
- [x] Vendor exact upstream definitions with attribution; copy all unique originals, leaving source assets intact.
- [x] Implement validation and normalization; rerun tests, commit.

### Task 2: Pure rendering and independent selection
**Files:** quickshell/appearance/{render,store}.py; tests/check_appearance_state.py.
**Interfaces:** render_theme(catalogue, selection) -> dict[str, bytes]; Store(path, catalogue).load(), .save(selection), .change(current, **fields); initial_selection(catalogue) -> dict.
- [x] Write/run failing tests for independent changes, read-without-write initialization, invalid JSON and IDs, backup/0600 state, TOML output, preserved legacy colors, and standalone lock CSS.
- [x] Implement the pure renderer and versioned state. Render all 36 Hyprstack variants; validate generated Niri includes in temporary configs.
- [x] Rerun catalogue/state tests and commit.

### Task 3: Preview controller and bridge
**Files:** quickshell/appearance/{service,bridge}.py; tests/check_appearance_service.py.
**Interfaces:** AppearanceService(root, state_dir, preview).snapshot(), .select(fields); bridge reads JSON requests and writes state/error events.
- [x] Write/run failing tests for staging/live rejection, temporary-root/session guards, independent palette/wallpaper application, serialized generations, partial failures, restart, and recovery.
- [x] Generate and validate candidates; update only isolated preview paths. Track requested and actually displayed wallpaper separately; errors are explicit.
- [x] Provide catalogue/state snapshots with local file URLs and no arbitrary command paths; rerun tests and commit.

### Task 4: Settings window and disposable preview
**Files:** quickshell/appearance-ui/{shell,ThemeGrid,WallpaperGrid}.qml; scripts/appearance-preview.py; appearance-preview.sh; docs/APPEARANCE.md.
**Interfaces:** JSON bridge actions: select (fields), state; settings IPC target appearance exposes status(), choosePalette(id, mode, accent), chooseWallpaper(id), page(name).
- [x] Add a real-window test/smoke flow: open both tabs, select dark/light/accent, change wallpaper, restart settings and verify persisted independent selection.
- [x] Implement keyboard-accessible grids/search, preview notice, progress/error presentation and lazy thumbnails.
- [x] Run isolated GUI preview; inspect screenshots and logs. Preserve the original preview and 77 dirty paths.
- [x] Update acceptance/results, run relevant original regressions and Niri validation, commit; request one fresh review of this feature.

## Execution rulings
- The user confirmed the design and asked to continue on 22 October; do not restart interviews about settled choices.
- Keep existing backend.py/shell.qml unmodified in this increment. Use a separate appearance bridge/window; connect the main menu when developing that menu. This avoids committing the pre-existing unrelated changes and keeps a small responsibility boundary.
- This deliverable prepares and demonstrates the feature. Installation activation/CLI routing, session startup and the dedicated Alacritty launch profile are connected in the separately authorized deployment/integration step; no live-apply command is offered here.

## Result

All four tasks completed in staging. 19 new Python tests, two QML keyboard behaviors, 39 original Python tests and three original regression scripts pass. Real GUI smoke at initial scale 1.6 confirms independent choices, GIF background and restart persistence. Scope is the guarded preview; installation and main-menu integration remain explicit follow-up work. Fresh review findings were reproduced and fixed, including the migration file path check.
