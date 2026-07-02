# Repo Hygiene Current Findings - 2026-06-30

Status: report-only findings.
Scope: `D:\code\ccode`, `D:\code\ccode\x64base`, and `C:\x64base`.

## Purpose

Record the current cleanup state without moving or deleting files. This note
keeps the possible `C:\x64base` relocation and root cleanup visible for future
AI agents and local scripts.

## Current Findings

`C:\x64base` exists, is readable, and is a backup git repo on:

```text
branch: upgrade/selfdoc-usage-contract
HEAD:   22db1c95a400ad30992721a532590ea131e4c52e
status: clean by git status --short
```

`D:\code\ccode\x64base` exists, is readable, and is the recent staged GitHub
x64base repo on:

```text
branch: upgrade/selfdoc-usage-contract
HEAD:   f2a9cc94c147f53922f880ec7835d03b3412b8f0
status: clean by git status --short
```

Derald confirmed that the `D:` x64base copy is the recent staged GitHub version,
while `C:\x64base` is a backup. The backup may be overwritten/refreshed from
the `D:` copy if Derald explicitly asks for that. The `D:` copy is not
disposable. Its recent commits include:

```text
f2a9cc9 Add reader manual package and DOCX preview
89efc8b Stage system message catalog and help/report message batches
887bfc8 Stage messaging catalog schemas and seed workflow
e5999fe Normalize selfdoc headers for support files
22db1c9 Release snapshot: normalize messaging help and metadata lanes
```

The `C:` x64base backup currently starts at `22db1c9` and does not include
those newer `D:` commits unless it is refreshed later from the `D:` copy.

## Root Noise Observed

The root of `D:\code\ccode` contains obvious local-only or generated artifacts,
including:

- root-level zip archives such as `dottalkpp.zip`, `data.zip`, `data (2).zip`,
  `drawio-libs-review.zip`, `indexes.zip`, and `lmdb.zip`
- screenshots named `Screenshot 2026-*.jpg`
- generated CMake files such as `CMakeCache.txt`, `build.ninja`,
  `cmake_install.cmake`, `CTestTestfile.cmake`, and `DartConfiguration.tcl`
- accidental flag-like files such as `--runtime-root`, `-Filter`, `-Pattern`,
  `=`, and `Unknown`
- temporary database output such as `tmpsql_regression.sqlite`
- patch/package files such as `*.patch` and package seed zips

These should be classified before movement. They should not be deleted in a
first pass.

## Existing Plan

The existing repo plan is `REPO_HYGIENE_PLAN.md`. It already sets the right
policy:

- no file deletion in the first pass
- no file moves without a checklist
- classify root files into keep, move, and review
- preserve source, tests, build config, stable docs, reusable scripts, and
  intentional tooling

## Recommended Next Pass

1. Generate a root-level relocation checklist with columns:
   `path`, `kind`, `recommended_action`, `destination`, `risk`, `reason`.
2. Treat `D:\code\ccode\x64base` as the active staged GitHub copy.
3. Treat `C:\x64base` as a backup unless Derald changes that decision.
4. Refresh/overwrite `C:\x64base` from `D:\code\ccode\x64base` only after an
   explicit request.
5. Move archives/screenshots/generated outputs only after approval.
6. Re-run `git status --short` after each narrow pass.

## Guardrail

Do not treat a noisy git tree as permission to reset, delete, or overwrite. The
noise contains both garbage and good artifacts.
