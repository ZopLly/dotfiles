# SDD ledger — plan: docs/superpowers/plans/2026-10-22-niri-appearance.md

Ruling: reuse user-selected standalone staging repository, branch staging; no new checkout.
Ruling: user explicitly approved the design and said the plan was settled; execute inline without another approval loop.
Pre-flight: catalogue -> renderer/store -> service -> GUI use the interfaces in the plan.
Ruling: independent appearance bridge leaves existing backend/shell untouched; menu integration follows in its own subsystem.
Task 1 RED: catalogue tests failed with ModuleNotFoundError before code existed.
Task 1: complete — catalogue tests 4/4 green; all 11 original images vendored; legacy source files untouched.
Task 2 RED: state/render test failed with missing appearance.render.
Task 2: complete — 8 catalogue/state tests green; 40 Niri appearance includes validate (4 legacy + 36 imported variants). State read is side-effect free, corruption refuses overwrite.
Task 3: complete — service tests 5/5 green; staging/wrong socket rejected, independent state/restart tested, disk-full before journal and after link both restored. Journal-before-directory-rename defect reproduced RED and fixed GREEN.
Task 4: complete — real GUI smoke passed at initial scale 1.6 in /tmp/niri-appearance-jxz9nm75; PNG completion verified before shutdown. QML keyboard RED -> GREEN (Enter previously did nothing); lint has 0 warnings/errors.
Final review: three Important findings reproduced RED and fixed GREEN: individual legacy file/migration containment; persisted unconfirmed wallpaper status with explicit recheck/reapply; backup recovery available in bridge/UI, corrupt bytes preserved.
Final tests: 58 Python tests (19 new + 39 original), three standalone original regression scripts, two QML keyboard behaviors pass. All 40 Niri color includes validate.
Preservation: original 77 pending paths unchanged except this feature's tracked brief; original theme SHA-256 values unchanged.
Ruling: fixed scale and floating settings rule are applied only in the disposable preview config, avoiding extra runtime window/output actions.
Ruling: keep branch staging locally; existing explicit instructions prohibit deployment/push without separate authorization, so no integration-choice prompt is needed.
Interview update: do not add a separate bottom calendar/music dashboard for now; retain center island.
