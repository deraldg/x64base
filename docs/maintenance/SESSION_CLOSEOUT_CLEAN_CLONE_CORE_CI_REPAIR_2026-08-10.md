---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260810-001
  recorded_at_utc: 2026-08-10T13:03:13Z
  agent:
    provider: OpenAI
    product: Codex
    model: GPT-5
    access_mode: local_write
  session:
    id: CODEX-20260810-001
    chat_reference: "codex-task:019fa118-fb90-7593-a062-2254c59b2306"
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 9efa31278860fc3679bd2422a06db6099eceb11f
    head_commit: 1bd7103d192c01677781ec6aa9f6d0acb1ecb303
  authorization:
    requested_by: maintainer
    scope: >
      Repair the failing public main CI, preserve the development-to-staging
      promotion boundary, verify Windows and WSL/Linux, and complete the cycle
      through a green GitHub Actions run.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_CLEAN_CLONE_CORE_CI_REPAIR_2026-08-10.md
    kind: session_closeout
---

# Session Closeout -- Clean-clone core CI repair (AIF-104)

Date: 2026-08-10.
Owning lifecycle: **x64base runtime SDLC**.
SDLC lane: `build-and-ci-repair`.
Truth state: source-defined cause, locally runtime-proven repair, remotely
runtime-proven publication.
Proof state: Windows/MSVC build and tests, WSL/GCC build and tests, native
case-sensitive Linux smoke, GitHub Actions run.

## One-line summary

Repaired the clean CORE/LEAN/NONE product composition, made the profile smoke
portable to native case-sensitive Linux, promoted only the necessary source
slice through `C:\x64base`, and closed on a fully green GitHub CI run.

## Cause and repair

The development build was green because it used a fuller product profile. A
clean CORE/LEAN/NONE checkout excluded external handlers and `xindex`, while
`shell_commands.cpp` still registered commands implemented only by those
excluded sources and `CdxDocument` still required the INX payload codec.

The repair:

- gates external command registrations on `DOTTALK_COMPONENT_EXTERNAL`;
- gates `SCX` registration on `DOTTALK_HAS_XINDEX`;
- owns `xindex/inx_payload.cpp` in a small internal static target shared by the
  lean shell and standalone BBS daemon when the full index engine is absent;
- launches the profile smoke from the application root so DATA is not doubled;
- uses the tracked `STUDENTS.dbf` and `STUDENTS.cnx` filename case so a native
  Linux checkout behaves the same as Windows and DrvFs.

No absolute development or staging drive path was added to source. No `.mdb`
file, database fixture, generated build product, or unrelated dirty-tree file
was promoted.

## Exact commits

| Surface | Commit | Contents |
| --- | --- | --- |
| development | `ab792d226` | product-selection/link repair, profile launch-root repair, AIF-104 registration |
| development | `1bd7103d1` | canonical fixture-case follow-up |
| staging/main | `473ffd894` | exact four-file source/test promotion |
| staging/main | `78f95ce2c` | exact one-file fixture-case follow-up |

`origin/development` ends at `1bd7103d1`; `origin/main` ends at `78f95ce2c`.
The two branches were not merged. Promotion was a named-file copy from the
development worktree into sterile staging.

## Verification

| Gate | Result |
| --- | --- |
| Development Windows `core-vcpkg` build | linked `dottalk_bbsd.exe` and `dottalkpp.exe` |
| Development Windows CTest | 13/13 passed |
| Development WSL/GCC `core-vcpkg` build | 441/441 units completed |
| Development WSL CTest | 13/13 passed |
| Native Linux case-sensitive `/tmp` smoke | `PASS: LEAN + NONE profile smoke` using uppercase-only fixtures |
| Staging fresh MSVC build | 442/442 units completed; both executables linked |
| Staging CTest | 13/13 passed |
| Staging install shape | executable, three INI files, license, two product manifests, LMDB DLL, SQLite DLL |
| Public-source policy | passed |
| Development and staging pre-push gates | passed for each exact slice and committed range |

The first published repair run, GitHub Actions
[`31388830290`](https://github.com/deraldg/x64base/actions/runs/31388830290),
proved the linker repair on both clean runners. Repository policy and the full
Windows job passed; Ubuntu configured and built, then exposed the lowercase
fixture spelling in profile test 11.

The follow-up GitHub Actions run
[`31389974256`](https://github.com/deraldg/x64base/actions/runs/31389974256)
is the publication proof:

- Repository policy: passed in 8 seconds.
- Ubuntu / GCC core: passed in 5 minutes 36 seconds.
- Windows / MSVC core: passed in 10 minutes 46 seconds, including tests,
  install shape, and artifact upload.

## Warning baseline

The compile warnings observed locally are pre-existing and remain tracked by
`docs/maintenance/WSL_LEAN_WARNING_BASELINE_2026-08-09.md`; this lane did not
silence, widen, or reclassify them. GitHub also reports that
`actions/checkout@v4` and `actions/setup-python@v5` target deprecated Node.js
20 and are being forced onto Node.js 24. That action-version warning is a
separate CI-maintenance follow-up; it did not fail any job or invalidate the
green build/test/package proof.

## Local build-tree note

The existing `C:\x64base\build\core-vcpkg` cache selected MinGW and therefore
was not accepted as MSVC evidence. It was preserved. The authoritative local
staging proof used the fresh ignored directory
`build/windows-msvc-core-staging-v6`, which identified MSVC 19.44 before
building. Earlier partial `windows-msvc-core-staging*` probe directories are
ignored local build output and are not repository content.

## Final state

- AIF-104: closed.
- Development: pushed and retains all unrelated shared-tree work untouched.
- Staging main: clean and equal to `origin/main` at `78f95ce2c`.
- GitHub CI: green on all three jobs.
- Release artifact: produced by the green Windows job with 14-day retention.

