# Session Closeout: ArcticTalk Regression and Environment Menu

Date: 2026-07-22.
Intake: AIF-049.
Parent project: `project.x64base.runtime`.
Lane: `arctictalk_tui_workbench`.
Change class: C1.
Baseline: `cc0761e8f32235251a43af91acadccd4b9771093`.

## Outcome

Added a compact ArcticTalk menu for environment selection and curated
regression access:

```text
Sys
  Environment / Tests
    Load x64 Environment (x64.dts)
    Load x32 Environment (x32.dts)
    List Regression Tests
    Run Regression Test...
    Run All Regression Tests...
```

Environment actions execute `DO X64` / `DO X32`. Regression listing executes
`REGRESSION LIST`. Selected and full regression actions prefill the command bar
and require explicit Enter/Run confirmation.

## Changed Source

- `include/tv/foxtalk_pro_menu_ids.hpp`
- `src/tv/foxtalk_menu.cpp`
- `src/tv/foxtalk_app.cpp`

New command ids were appended to preserve the numeric values of existing menu
ids.

## Governance Records

- `docs/maintenance/ARCTICTALK_MENU_REGRESSION_ENVIRONMENT_PREFLIGHT_2026-07-22.md`
- `docs/maintenance/ARCTICTALK_RETRO_TUI_WORKBENCH_LANE_V1.md`
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`
- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`

## Proof

Builds:

```powershell
cmake --build D:\code\ccode\build --target dottalk_tvui --config Release
cmake --build D:\code\ccode\build --target dottalkpp --config Release
```

Both passed. Final executable:

```text
D:\code\ccode\build\src\Release\dottalkpp.exe
```

Non-destructive command-path smoke:

```text
REGRESSION LIST
DO X64
SET PATH
DO X32
SET PATH
EXIT
```

Results:

- curated regression registry listed 24 entries;
- `DO X64` set DBF, INDEXES, and LMDB to the x64 paths;
- `DO X32` set DBF and INDEXES to the x32 paths;
- process exited 0;
- no regression suite was executed.

## Finding

The current `x32.dts` does not set LMDB. When it follows `DO X64`, the LMDB
path remains x64. This is existing environment-script behavior, not introduced
or repaired by the menu slice. It remains a separate review item.

## Scope Boundary

No environment `.dts`, regression registry, GUI workbench, data, HELP,
publication, or staging file was changed. This menu is `tui-adapted` under
AIF-049 and does not alter the synchronized wx/Python open GUI API.

Interactive visual selection of the compiled menu remains pending; source
wiring, compile/link, and underlying command paths are proven.
