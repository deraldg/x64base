# ArcticTalk Turbo Vision Grid Browser Preflight

Date: 2026-07-22.
Parent project: `project.x64base.runtime`.
Lane: `arctictalk_tui_workbench` / AIF-049.
Change class: C1 - localized, reversible integration and navigation repair.

## Source Mutation Rule

Target source files:

- `src/tv/cmd_recordview.cpp`
- `src/tv/foxtalk_app.cpp`
- `src/tv/foxtalk_menu.cpp`
- `src/tv/foxtalk_shell_bridge.cpp`

Owning subsystem:

- ArcticTalk Turbo Vision workbench under DotTalk++ / x64base.

Baseline commit:

- `cc0761e8f32235251a43af91acadccd4b9771093`
- `src/tv/cmd_recordview.cpp` and `src/tv/foxtalk_shell_bridge.cpp` were clean
  before this slice.
- `src/tv/foxtalk_app.cpp` and `src/tv/foxtalk_menu.cpp` already contained the
  uncommitted AIF-049 environment/regression menu slice. This change must
  preserve it.

Owning lifecycle and SDLC lane:

- `project.x64base.runtime`
- `arctictalk_tui_workbench` / AIF-049

Truth state, proof state, risk class, and next gate:

- Truth: maintainer requested a table grid browser inside the TVision
  workbench.
- Proof: existing `BROWSETV` source inspected; build and interactive runtime
  proof pending.
- Risk: C1; read-only table display, with the documented side effect of moving
  the current work-area record cursor.
- Next gate: integrate the existing browser into ArcticTalk, compile, then
  verify routing and navigation behavior.

Contracts read:

- `AI_PORTAL.md` Source Mutation Rule.
- `docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`.
- `docs/maintenance/ARCTICTALK_RETRO_TUI_WORKBENCH_LANE_V1.md`.
- `docs/governance/REPO_BOUNDARIES_RUNTIME_GUI_LABTALK_v1.md`.

Applicable `@dottalk.contract` / `@dottalk.usage` blocks:

- `src/tv/cmd_recordview.cpp` - `@dottalk.usage v1` for `BROWSETV`.
- No local `@dottalk.contract` block exists in the target files.

Constraints and conflicts:

- Reuse the existing `BrowseGridWindow`; do not start a nested TVision
  application and do not add a second database-browser implementation.
- Keep the first integrated slice read-only. Moving the active record cursor
  remains allowed and documented.
- Show all table fields through horizontal scrolling instead of silently
  dropping fields outside the initial window width.
- Deleted records remain hidden by default and visible through the existing
  `ALL` toggle.
- Keep `BROWSETUI` as an outer-CLI-only surface.
- Do not modify the wx or Python/Tkinter workbenches. This is a classified
  `tui-adapted` workbench feature, not an open-GUI-API contract change.
- Do not update `CURRENT_TARGET.md`; AIF-049 is a parallel lane.

Expected behavior change:

- `BROWSETV` entered at the ArcticTalk command bar opens a child grid window on
  the current desktop.
- Browse -> Browse Current Table and Browse -> Turbo Vision Grid Browser open
  that same integrated grid.
- The grid shows a fixed record-number/deletion prefix and all fields, with
  horizontal scrolling when needed.
- Up, Down, Page Up, Page Down, Home, and End move and visibly highlight the
  selected record.
- Enter opens the selected record in the existing read-only record window.
- `A` toggles deleted-record visibility; `R` reloads; Esc closes.

Proof/test plan:

1. Build `dottalk_tvui` and `dottalkpp` in Release configuration.
2. Confirm `BROWSETV` is no longer classified as a nested TVision app.
3. Confirm both relevant Browse menu commands route to `BROWSETV`.
4. Confirm the grid reloads and highlights after each navigation action.
5. Run `git diff --check` on the scoped source and evidence files.
6. Record interactive visual verification separately if terminal automation
   cannot safely drive the full-screen TVision application.
