# Applications implementation plan

> REQUIRED SUB-SKILL: superpowers:executing-plans; inline execution.

**Goal:** Working integrated application island and launcher in disposable Niri preview.
**Spec:** ../specs/2026-10-22-niri-applications.md
**Architecture:** Python applications model/service and JSON-lines event bridge; QML controller, icon buttons and drawer integrated by small additions to existing Bar/shell. Reuse the strict appearance preview boundary. Gio desktop metadata exported before isolating HOME. Existing dirty changes must remain unstaged.

## Global Constraints
Only niri-staging. Preserve original colors/assets and unrelated dirty files. No live apply, installs, push, SSH keys or restarts. Save baseline and stage only additive integration hunks. Continue agreed work without further approval loops.

## Review Focus
Window/desktop identity, ambiguous matching and stale windows; popup keyboard focus and narrow widths; native actions only on private socket; unsafe launch blocked; process exit and event-stream reconnect; unchanged dirty baseline and appearance preview regressions.

### Task 1: Model and guarded service
**Files:** quickshell/applications/*.py, dev/tests/check_applications.py.
**Interfaces:** desktop_entries(); groups(entries, windows, workspaces, current_only, output); ApplicationService.snapshot/action. Preview boundary shared with appearance.
- [x] Write/run failing behavior tests for matching, grouping, workspace filter, stale IDs, unsupported actions and preview guard.
- [x] Implement service/event bridge, Gio catalogue and safe preview terminal/settings launch; rerun tests and commit.
Expected: tests pass, no writes or native commands outside disposable preview.

### Task 2: Island, launcher and real GUI verification
**Files:** quickshell/Applications*.qml, AppIcon.qml, ApplicationsLayout.js; small Bar/shell integration; scripts/applications-preview.py; dev/tests/qml/tst_applications.qml; docs/APPLICATIONS.md.
**Interfaces:** controller with entries/groups/action; shared root openPanel/openScreen; IPC applications status/menu/act; settings appearance IPC.
- [x] Write/run failing QML keyboard/layout tests and preview smoke before implementation.
- [x] Implement compact island, overflow, window actions and searchable menu. Add isolated preview including settings.
- [x] Verify actual windows focus/fullscreen/close and menu/settings handoff; inspect screenshots; run original regressions and Niri validation.
- [x] Commit only this feature, run one fresh final review and fix important findings. Document results and remaining limitations.
Expected: real preview works at scale 1.6, no GUI errors, original dirty baseline preserved.

## Result
Both tasks complete. Three final review findings fixed with reproductions. Verification: 77 unittest cases, six standalone regression scripts, 19 QtTest results, zero QML lint diagnostics, Niri validation and both real nested GUI smoke flows. Installed session unchanged; local staging commits retained.
