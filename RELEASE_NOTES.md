# x64base 1.1 (beta 1.b) -- release notes

Tag `v1.1.0-beta`. This is an evaluation release of the DotTalk++ / x64base
educational DBF runtime. It is not production-ready and is not a drop-in
replacement for a commercial xBase product.

## Included

- Windows x64 runtime built from the `pro-md` preset -- the build `BUILDING.md`
  recommends: LMDB indexing and the Turbo Vision UI. The binary is built from
  the same source as the tag.
- Runtime data: the sample databases (MCC x32, VFP and x64 lanes), scripts and
  help tables.
- Source archive supplied automatically by GitHub.
- SHA-256 checksum for the Windows ZIP.

## First run

Unzip, then start DotTalk++ with the launcher in the unzipped folder. The first
time, add `-FirstRun` to build the x64 LMDB indexes (they are derived files and
are not shipped):

```powershell
.\start.ps1 -FirstRun
```

`start.cmd` does the same for cmd.exe or a double-click, without the index
build. From it, run `DO scripts\mcc\mcc_build_x64_lmdb.dts` once inside the
shell and then `CLOSE ALL`: the build leaves all twelve x64 tables open, so a
following `USE STUDENTS` would report the table as already open.
Then, at the DotTalk++ prompt:

```text
DO X64
USE STUDENTS
SET INDEX TO STUDENTS
SET ORDER TO TAG LNAME
SMARTLIST 10
```

Record 1 by `LNAME` should read `Anderson`.

## Shell commands are off by default

`!` (run a host command), and the SFTP and SMTP helpers, are refused out of the
box: the runtime starts as the unauthenticated `member.public`, and host
commands also require an explicit opt-in. To see where you are without the
shell, use `PWD` (working directory, DATA and DBF slots) or `SETPATH` with no
arguments. To enable host commands for one session, deliberately:

1. Set `DOTTALK_ALLOW_HOST_COMMANDS=1` in the environment before starting, for
   example `$env:DOTTALK_ALLOW_HOST_COMMANDS = '1'; .\start.ps1`.
2. Act as an identity that holds `host.shell`: the owner, or a member the owner
   granted it with `USER GRANT host.shell TO <member>`. See `USER USAGE`.

Both are required; neither alone enables `!`. Leave them off unless you need
them.

## Verified for this build

- Fresh clone of `main`, Windows: `pro-md` configures and builds; the demo
  databuild creates the three MCC lanes (STUDENTS 200 records); the quickstart
  returns `Anderson`; `REGRESSION CURATED SUITE` passes 34/34.
- The installed package (`cmake --install`), after the first-run step above:
  quickstart returns `Anderson`; curated suite 34/34.
- Windows (MSVC) and WSL (`wsl-lean`) both build and run from the same tree.

## Known limitations

- No atomic transaction guarantee spans DBF, memo, and index persistence.
- wxWidgets (the Workbench GUI) and the Python bindings are optional lanes and
  are not in this artifact; build them from source per `BUILDING.md`.
- The ctest profile smoke can fail on a machine where an unrelated `data`
  folder sits above the build directory: the runtime looks for `data` by
  walking up from the executable before trying the working directory.
- x64 widening is not yet proven for every command and index backend.
- Only `pro-md` and `windows-core` have been built from a fresh clone; the
  other edition presets (`windows-lean-*`, `windows-educational-lmdb`,
  `windows-development-lmdb`) have not been cold-clone certified.
- Back up data before evaluation and use disposable copies for mutation tests.
- Localization is partial: with `SET LANGUAGE TO it` (or es/fr/de) some
  report headings and labels still print in English.
- The cursor footer after `LIST` reads `Area 8 of 0 ... 511`, meaning area 8 of
  the slot range 0 to 511; the wording is being clarified.

## License

Dual-licensed: **GPL-3.0-only** (`LICENSE`), free for everyone, or a separate
commercial license for closed or proprietary use. Educational and
non-commercial use is free under the GPL. Terms: `LICENSING.md` and
<https://x64base.com/licensing/>.
