# Session Closeout — Cold-Clone Journey Certification (2026-07-15)

Status: **certified.** A fresh clone of `main` builds, runs, and answers —
the full stranger journey, proven end to end from `C:\scratch\dudetest`.

## What this session proved

The question was "is ours valid?" — can a stranger clone the public repo and
get a working database. The answer is now demonstrated, not hoped:

```
clone  ->  cmake --preset pro-md + build  ->  datarun (stages exe+DLLs)
       ->  build_mcc_demo_bases.ps1  (reset -> extract -> x32 -> vfp -> x64 -> LMDB)
       ->  ordered query
```

Every path in the certifying run read `C:\scratch\dudetest`. The engine
reported `730434d2` (the clone's own build, clean), not the dev binary.

## Evidence (assert the data AND the source)

- **Location-honest.** `[1/3] Root: C:\scratch\dudetest`; `[3/3] BIN:
  C:\scratch\dudetest\dottalkpp\bin`; runtime `dottalk++ v0.6 730434d2` — the
  clone's own exe, not dev's `fecc3951`.
- **Freshness assertion, all three lanes.** `STUDENTS` = 200, record 1 under
  TAG SID = `50000000 Taylor Quinn`; `ENROLL` = 686; `TEACHERS` = 20.
- **Real rebuild, not a reindex.** Every `CNX CREATE` / `CDX CREATE` reported
  `created:`, never `file already exists`.
- **LMDB built by the script.** `BUILDLMDB CLEAN YES` built all 12 x64 envs
  (128 MiB each) unattended — no hand-walking of areas.
- **Ordered reads from the clone's own LMDB.** demo tour: `SMARTLIST` by LNAME
  starts at `Anderson`; `DESC` starts at `Wilson`; `LIST FOR LNAME = WHITE`
  runs in `MODE LMDB`; `ENROLL` child ordered by SID.

## What made it true (four fixes)

All in DEV this session. Two publication channels (see below).

1. **`launch-common.ps1`** (git-channel) — `Update-DotTalkRuntimeExe` asserted
   the *destination* exe before copying to it, so a clone (empty `bin/`, `*.exe`
   gitignored) threw "Runtime executable path not found." Fixed to assert the
   *source* build output, create `bin/` if absent, stage the exe, **and stage
   the full runtime DLL set** (lmdb, sqlite3, tvision, transitive) from the
   exe-adjacent dir + vcpkg bin. Also generalized `BuildExe` to find the newest
   `dottalkpp.exe` across build roots.
2–4. **`build_mcc_demo_bases.ps1`, `reset_mcc_fixtures.ps1`,
   `extract_mcc_og.ps1`** (manifest) — each defaulted `$Root = "D:\code\ccode"`,
   so run from a clone they operated on the *dev* tree. Fixed to derive the repo
   root from the script's own location (`$PSScriptRoot`, three parents up).

## Root lesson

A released entry point must resolve its own location, never hardcode a dev
path. The same class of bug appeared twice — in the launcher (exe path) and in
the databuild scripts (repo root). Both masked themselves on the maintainer's
machine (dev tree present) and only surfaced on a genuine cold clone. The
cold-clone test is the only test that catches it. Recorded in
`LOCAL_ACCESS_AGENT_CHECKLIST_V1.md`.

## Publication — not yet on `main`

Only the local dev tree and the `C:\scratch\dudetest` clone have these fixes.
To make a fresh GitHub clone inherit them:

- **`launch-common.ps1`** reaches `main` through git (source/tooling channel,
  like `datarun.ps1` and `src/`) — a commit to `main`, cold-clone re-verified.
- **`dottalkpp/scripts/mcc/*.ps1`** reach `main` through `PROMOTE.manifest` /
  `rebuild-staging.ps1`.

Both channels must go out; the clone-copy done this session only proved them.

## Open / deferred

- **BibleTalk startup quote** fails on a clone (`biblebase\*.sqlite` seed not
  published). Degrades gracefully; decide whether to ship the seed or quiet the
  message. Cosmetic.
- **`ver` alias.** `version` works, `ver` is unknown — a one-line alias would
  catch the reflex. Cosmetic.
- **vcpkg env-var split** (`VCPKG_ROOT` vs `VCPKG_INSTALLATION_ROOT` across
  presets) — documented-around in `BUILDING.md`; real reconciliation is a
  CMakePresets change (Path A / a targeted `main` edit).
- **x64 ordered read with missing LMDB** silently falls back to physical order
  after printing "LMDB env missing" — belongs with the `SETLMDB`/`BUILDLMDB`
  runtime findings (source-gated).
- **Path A (editions)** — the certification *method* is now proven end to end
  for `pro-md`; the edition presets still need the same treatment (see
  `EDITION_PUBLICATION_PLAN_A_V1.md`).

## Report by stage

Dev changed: `launch-common.ps1`, three `mcc/*.ps1`, BUILDING.md, the Plan A
doc, the checklist, the intake queue, this closeout. Promoted to staging: not
yet. Validated: cold-clone build + full databuild + ordered query, all green
under a fresh clone. Pushed: not yet (maintainer git step).
