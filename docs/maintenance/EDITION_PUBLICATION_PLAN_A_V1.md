# Edition System Publication Plan (Path A) v1

Status: **plan — not yet executed.**
Date: 2026-07-14.
Owning lifecycle: DotTalk++ SDLC (build + publication).
Depends on: Path B (honest `BUILDING.md`) published first.

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
4. **Certify with a COLD CLONE.** This is the gate. From a fresh clone of the
   branch, on a clean machine:
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
5. **Merge to `main`** only after the cold clone is green.
6. **Flip `BUILDING.md`** — replace the "Editions (in development)" section with
   the real product × index-mode tables and the `windows-*` build commands.
   Now the doc follows proven source, which is the correct order.
7. **Reconcile the vcpkg env-var split** while here: presets disagree
   (`VCPKG_ROOT` vs `VCPKG_INSTALLATION_ROOT`). Pick one and update all presets,
   or document both. A fresh cloner setting only one currently fails half the
   presets.

## Definition of done

- A cold clone of `main` builds `dottalkpp.exe` from a documented `windows-*`
  preset with no undocumented prerequisites.
- `BUILDING.md` describes only presets that exist on `main` (now including the
  editions).
- The edition proof records (`XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` etc.) no
  longer reference presets absent from `main`.
- `dudetest` (the cold-clone build) is recorded as passing in a session
  closeout.

## Not done here

This plan is written; it is not executed. Executing it requires the maintainer
(and ideally the original engine author) on a build machine. An AI agent should
not hand-assemble the source changeset or claim the build passes without the
cold-clone certification above.
