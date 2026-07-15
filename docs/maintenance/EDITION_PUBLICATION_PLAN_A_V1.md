# Edition System Publication Plan (Path A) v1

Status: **plan — not yet executed.**
Written: 2026-07-14. Updated: 2026-07-15.
Owning lifecycle: DotTalk++ SDLC (build + publication).
Depends on: Path B — **done and certified** (see Status Update below).

## Status Update — 2026-07-15

Two things changed since this plan was written, and both make Path A more
concrete, not less:

1. **Path B is published and cold-clone certified.** `BUILDING.md` is honest on
   `main` (commit `730434d2`). More importantly, the certification *method* this
   plan depends on is no longer theoretical — it was executed end to end:
   a fresh clone of `main` ran `cmake --preset pro-md` (configure, 29.7s, vcpkg
   restored tvision/sqlite/nlohmann_json) and `cmake --build --preset
   pro-md-Release --target dottalkpp`, producing
   `build/src/Release/dottalkpp.exe` from `730434d2 dirty=0`. So the cold-clone
   gate below is a proven procedure; Path A just runs it against the *edition*
   presets instead of `pro-md`.

2. **"Builds the exe" is not the finish line — the full journey is.** A stranger
   who builds `dottalkpp.exe` still has to **set up the runtime environment and
   build the databases and indexes from the scripts** before anything is
   testable. The published DBFs and CDX/CNX indexes are in a clone, but the LMDB
   environments are gitignored (derived, 53 GB) — so a fresh clone genuinely
   cannot exercise the full x64 LMDB path until it runs the databuild. "Valid
   for a stranger" therefore means the whole arc — build → runtime setup →
   databuild → query — not just a green compile. The Definition of Done below is
   expanded accordingly.

3. **The vcpkg env-var split is confirmed real.** The certified `pro-md` build
   needed `VCPKG_ROOT`; other presets read `VCPKG_INSTALLATION_ROOT`. Setting
   only one fails half the presets. Reconciling this is still a Path A task
   (step 7).

4. **The FULL journey is now certified for `pro-md`, not just the build.** On
   2026-07-15 a fresh clone went clone -> build -> `datarun` -> databuild ->
   ordered query, entirely under the clone root, running the clone's own
   `730434d2` exe. This required fixing two location-honesty bugs that only a
   cold clone exposes: `launch-common.ps1` asserted (and failed on) the
   destination exe instead of staging the source build output + its DLLs; and
   `build_mcc_demo_bases.ps1` / `reset_mcc_fixtures.ps1` / `extract_mcc_og.ps1`
   defaulted `$Root` to a hardcoded dev path. See
   `SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md`. The Definition
   of Done's "build -> runtime setup -> databuild -> query" arc is therefore a
   demonstrated procedure; Path A runs the same arc against the edition presets.
   These prerequisite fixes are now published on `main`: the location-honest
   launcher and MCC journey in `46e021594bee25fd40fe9b79e318c691e1a714a0`,
   followed by the valid DotScript `&&` banner correction in
   `b9d480215c036178ba99b5109a8a2489ee89b215`.

## Why this plan exists

The edition build system — products `LEAN` / `PROFESSIONAL` / `EDUCATIONAL` /
`DEVELOPMENT`, index modes `NONE` / `LEGACY` / `LMDB`, and the `windows-*`
presets — exists in development (Codex's engine-edition-separation work) but is
**not on `main`**. A cold clone of `main` has only the older presets
(`core`, `pro-md`, `index-vcpkg`, `wsl`, ...). Its `CMakePresets.json` uses
`DOTTALK_WITH_INDEX`, not `DOTTALK_PRODUCT` / `DOTTALK_INDEX_MODE`.

Path B (done) made `BUILDING.md` honest about that gap. Path A closes it by
publishing the edition system itself, certified.

## Why the manifest is NOT the tool here

Engine source and build config do not travel through `PROMOTE.manifest` /
`rebuild-staging.ps1`. That overlay carries development's *current* file state,
and the working tree holds experimental uncommitted changes. Source must publish
as a **coherent, build-tested git changeset**. See
`labtalk/ai_portal/PROMOTION_MODEL_SEED_V1.md` -> "The manifest does NOT carry
engine source".

## The coherent changeset

These must move to `main` **together**, or the build breaks:

- `CMakePresets.json` — the new `windows-lean-*`, `windows-educational-lmdb`,
  `windows-development-lmdb` presets.
- `CMakeLists.txt` — `DOTTALK_PRODUCT`, `DOTTALK_INDEX_MODE`, the component
  resolution, and the `DOTTALK_HAS_XINDEX` compile definitions.
- `src/` edition guards — every `#if`/`#ifdef DOTTALK_HAS_XINDEX` (and related)
  branch the modes depend on, plus the `xbase` / `xindex` separation
  (`xbase.lib` neutral hooks; `xindex.lib` provider).
- Any `src/tests/` and `CTest` registrations named in the proof matrix
  (`dottalkpp_profile_smoke`, `dottalkpp_lmdb_backend_smoke`,
  `package_manifest_*`).
- The package-manifest allow-lists referenced by those tests.

**Do not hand-pick these by eye.** The authoritative source of the changeset is
Codex's committed engine-edition work in development. Identify it by diffing the
edition-work commit range against `main`, not by guessing file lists. A missing
guard yields a clone that configures but fails to compile a given mode.

## Procedure (maintainer / operator run)

1. **Identify the changeset.** In development, find Codex's edition-separation
   commits (see the two `SESSION_CLOSEOUT_X64BASE_ENGINE_EDITION_SEPARATION_*`
   records). Confirm the set builds locally in development for at least
   `NONE`, `LEGACY`, and `LMDB`.
2. **Branch off `main`.** `git switch -c edition-system origin/main` in a clone
   or the staging tree. Never build the edition changeset directly onto the
   published `main` before it is certified.
3. **Apply the changeset** to the branch — cherry-pick the commits, or apply a
   reviewed diff. Keep it to the build system + guards + tests; no unrelated
   dev churn.
4. **Certify with a COLD CLONE.** This is the gate, and the procedure is
   proven — it was run for `pro-md` on 2026-07-15 and produced a working exe.
   Run the same steps against the edition presets. From a fresh clone of the
   branch, on a clean machine (with `VCPKG_ROOT` set — see step 7):
   ```powershell
   cmake --preset windows-lean-table
   cmake --build --preset windows-lean-table --target dottalkpp pydottalk
   ctest --preset windows-lean-table
   cmake --preset windows-development-lmdb
   cmake --build --preset windows-development-lmdb --target dottalkpp
   ```
   All must configure, build, and pass. A build on the developer's own machine
   is not this test — it must be a fresh clone, because that is what a stranger
   gets. This is a long, maintainer-operated build (operator-handoff rule).
   Then continue past the compile to the **full journey** (see Definition of
   Done): run the databuild from the same clone and query it. A build that
   compiles but whose databuild or runtime fails is not certified.
5. **Merge to `main`** only after the cold clone is green.
6. **Flip `BUILDING.md`** — replace the "Editions (in development)" section with
   the real product × index-mode tables and the `windows-*` build commands.
   Now the doc follows proven source, which is the correct order.
7. **Reconcile the vcpkg env-var split** while here: presets disagree
   (`VCPKG_ROOT` vs `VCPKG_INSTALLATION_ROOT`). Pick one and update all presets,
   or document both. A fresh cloner setting only one currently fails half the
   presets.

## Definition of done

The full stranger journey, proven from a cold clone — not just a compile:

- A cold clone of `main` **builds** `dottalkpp.exe` from a documented `windows-*`
  preset with no undocumented prerequisites.
- From that same clone, the stranger **sets up the runtime environment and
  builds the databases and indexes** via `dottalkpp/scripts/mcc/
  build_mcc_demo_bases.ps1` — including the LMDB environments, which are not
  shipped and must be generated.
- From that same clone, the built runtime **runs and answers a query**
  (`USE STUDENTS` / `SET ORDER TO TAG LNAME` / `SMARTLIST 10` returns the
  roster).
- `BUILDING.md` describes only presets that exist on `main` (now including the
  editions), **and** its "After the build" section spells out the runtime-setup
  + databuild step clearly enough that the stranger is never stranded between a
  built exe and a working query.
- The edition proof records (`XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` etc.) no
  longer reference presets absent from `main`.
- The vcpkg env-var split is reconciled (one variable, or both documented).
- The whole run — build, databuild, query — is recorded as passing in a session
  closeout, the way the `pro-md` cold-clone build was on 2026-07-15.

## Not done here

This plan is written; it is not executed. Executing it requires the maintainer
(and ideally the original engine author) on a build machine. An AI agent should
not hand-assemble the source changeset or claim the build passes without the
cold-clone certification above.
