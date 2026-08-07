# ArcticTalk Regression and Environment Menu Preflight

Date: 2026-07-22.
Parent project: `project.x64base.runtime`.
Lane: `arctictalk_tui_workbench` / AIF-049.
Change class: C1 - localized, reversible implementation change with a narrow
interface.

## Source Mutation Rule

Target source files:

- `src/tv/foxtalk_menu.cpp`
- `src/tv/foxtalk_app.cpp`
- `include/tv/foxtalk_pro_menu_ids.hpp`

Owning subsystem:

- ArcticTalk Turbo Vision workbench under DotTalk++ / x64base.

Baseline commit:

- `cc0761e8f32235251a43af91acadccd4b9771093`
- All three target source files were clean before mutation.

Owning lifecycle and SDLC lane:

- `project.x64base.runtime`
- `arctictalk_tui_workbench` / AIF-049
- Companion evidence lane: BETA-1 stabilization/regression / AIF-041

Truth state, proof state, risk class, and next gate:

- Truth: source change authorized by maintainer request.
- Proof: pending targeted build and command-routing inspection.
- Risk: C1; menu wiring only, but selected scripts/tests may mutate session,
  data, or files according to their own contents.
- Next gate: compile the ArcticTalk TV units, then inspect the exact menu-to-
  command mappings.

Contracts read:

- `AI_PORTAL.md` Source Mutation Rule.
- `docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`.
- `docs/maintenance/ARCTICTALK_RETRO_TUI_WORKBENCH_LANE_V1.md`.
- `docs/governance/REPO_BOUNDARIES_RUNTIME_GUI_LABTALK_v1.md`.

Applicable `@dottalk.contract` / `@dottalk.usage` blocks:

- `src/cli/cmd_regression.cpp` - `@dottalk.usage v1` for `REGRESSION`.
- `src/cli/cmd_dotscript.cpp` - `@dottalk.usage v1` for `DOTSCRIPT`.
- No local `@dottalk.contract` block exists in the three ArcticTalk target
  files.

Constraints and conflicts:

- Use the normal ArcticTalk `runImmediate` / `prefill` dispatch path, which
  reaches the canonical shell executor.
- `DO X64` and `DO X32` are xBase-style aliases resolved to `DOTSCRIPT`.
- `x64.dts` and `x32.dts` set environment paths and mutate session state.
- `REGRESSION ALL` may run scripts with broader mutations. Selecting its menu
  item must prefill the command and require an explicit Enter/Run action.
- Do not add a separate script runner.
- Do not modify the environment scripts or regression registry.
- Do not modify the wx or Python/Tkinter workbenches; this is a classified
  `tui-adapted` ArcticTalk surface, not an open-GUI-API change.
- Do not update `CURRENT_TARGET.md`; AIF-049 is a parallel lane.

Expected behavior change:

- ArcticTalk's System submenu exposes named `x64.dts` and `x32.dts`
  environment actions.
- The same submenu exposes curated regression list, selected-test, and
  full-suite actions.
- Environment actions execute immediately through `DO X64` / `DO X32`.
- Regression list executes immediately.
- Selected-test and full-suite actions prefill the command bar for explicit
  confirmation.

Proof/test plan:

1. Build the configured target containing `dottalk_tvui`.
2. Confirm each new command id is present in the enum, menu, and dispatch.
3. Confirm the command strings match documented `REGRESSION` and DotScript
   syntax.
4. Run `git diff --check` on the scoped change.
5. Do not run `REGRESSION ALL` merely to prove menu wiring.
