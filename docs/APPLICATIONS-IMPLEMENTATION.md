# SDD ledger — plan: docs/superpowers/plans/2026-10-22-niri-applications.md
Ruling: Continue previously approved design; this spec records agreed behavior, no new approval required.
Ruling: Existing staging checkout is user-selected isolation; no additional worktree.
Ruling: Baseline dirty files retained; integration changes will be staged via feature-only patch against HEAD, never whole-file add.
Pre-flight: Task1 emits catalogue/state/actions; Task2 controller consumes catalogue once, groups and errors thereafter. Same JSON fields documented in module.
Pre-flight: Task2 uses existing openPanel/openScreen exclusive drawer state; no independent simultaneous popups.
Task 1: complete (commits d31c833..260656a, tests: python3 tests/check_applications.py → OK)

Task 2: GUI smoke reproduced JSON channel corruption from settings child stdout; failing regression added. Child diagnostics redirected to stderr. All action/window changes were in disposable Niri only.
Ruling: Error banner keeps its own input region even after launcher closes; real GUI screenshot included. Drawer height follows content instead of empty fixed rectangle.
Verification: generic system-python calendar test initially failed (missing icalendar); rerun using its existing calendar-venv as production launcher selects. No package installation.

Final review: /root/applications_review, read-only d31c833..2d70ab2. Accepted P2 findings: case-distinct desktop IDs, disappearing overflow at 500..515 logical pixels, invisible list keyboard selection. All three reproduced RED and fixed GREEN in one consolidated pass. Highlight regression strengthened to require actual painted color, not Qt's default empty highlight item.
Declined review topics accepted: real app launch, installation and minimization explicitly deferred; pre-existing dirty changes excluded; backend death reports stopped-service error; no additional concrete lifecycle/Escape/outside-click failure found.
Verification: 77 unittest cases across 15 scripts; six standalone regression scripts; 19 QtTest results (11 behavior cases + setup/cleanup); qmllint zero diagnostics; Niri validate; real applications GUI smoke plus appearance GUI smoke both pass. Calendar uses existing production calendar-venv (system Python lacks its optional icalendar dependency); no install or skipped test.
Preservation: reverse only the committed Bar/shell feature -> byte-for-byte baseline copies. All other pre-existing tracked content and dirty path list unchanged. A naive diff comparison initially failed solely because repeated closing braces aligned differently; exact reversal proves preservation.
Ruling: Keep local commits in the user's staging repository, as explicitly requested; no merge/publish/install menu. No worktree was created. User can review the integrated preview before separately authorizing deployment.
Task 2: complete (commits 260656a..395efc4, tests: python3 -m unittest discover -s tests -p check_applications*.py → OK)
