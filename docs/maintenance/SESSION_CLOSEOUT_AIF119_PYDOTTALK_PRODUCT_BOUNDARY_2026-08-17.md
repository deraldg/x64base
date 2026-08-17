---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260817-COWORK-002
  recorded_at_utc: 2026-08-17T20:05:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: c804aff71
  authorization:
    requested_by: maintainer (member.derald), in-session, "make a version were lmdb is included"
    scope: >
      Afternoon session. Opens AIF-119 and charters pydottalk as a separate
      co-sourced product. Records the LMDB index-mode measurement, a build
      defect found by changing a default, and a coordination defect that made
      the house safety check blind to new files.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AIF119_PYDOTTALK_PRODUCT_BOUNDARY_2026-08-17.md
    kind: session_closeout
---

# Session Closeout -- AIF-119: pydottalk gets a product boundary

Date: 2026-08-17 (afternoon). Owning lifecycle: SDLC (new).
SDLC lane: build / packaging / coordination. **AIF-119**, claimed this session
(run `COWORK-20260817-001`, lane `pydottalk-co-sourced-product`).
Charter: `docs/maintenance/AIF_119_PYDOTTALK_CO_SOURCED_PRODUCT_LANE_V1.md`.
Continues `SESSION_CLOSEOUT_AIF118_CONSOLE_THEME_LAB_AND_LEAN_PYDOTTALK_2026-08-17.md`
(same day, morning).

## What landed

| commit | what |
| --- | --- |
| `1655e2fc1` | `bindings/pydottalk/CMakePresets.json`; `DOTTALK_HAS_XINDEX` no longer contradicts `xindex` |
| `e7cfc3429` | SDLC charter, `projects.yaml` registration, two build proofs, OI-007 |
| `a98fe8c37` | `-uall` required in `CLAUDE.md`, `AI_README.md`, the Tier 1 seed; OI-008, OI-009 |
| `04a2ae93a` | OI-008 extended with four measured costs |
| `827e5d065` | AIF-119 lane charter, intake row, claim file |
| `e65c0cdf1` | charter's `pyproject.toml` claim corrected |

## The question asked, and the answer it turned into

The ask was "make a version where lmdb is included". Two owner corrections
redirected it inside the first minute: **"that would be a cmake option"** (it
already was -- `DOTTALK_INDEX_MODE`, defaulting to LMDB) and **"there is an
example already with our lean version with lmdb on github main"** (there is --
the `wsl-lean` preset). I had searched `development` by filename and concluded
no prior art existed, then accepted an "I stand corrected" that was not owed.
**Look on the branch that was named before answering.**

What the measurement then found:

- **LMDB mode compiles and links on Linux/ELF.** `lmdb_backend.cpp.o` builds.
  That closes the one path the morning run could not reach.
- **It changes nothing that ships.** LMDB, LEGACY and NONE produce a
  byte-identical module: 665336 bytes, sha256 `54cb15eb...`, three times.
  Corroborated rather than inferred from size: zero `mdb_` symbols, zero
  undefined index symbols, and `ldd` lists only libc, libstdc++, libgcc, libm.
- **The build tree differs and the artifact does not**: 48 / 47 / 25 objects.
  A static archive contributes only objects that resolve an undefined symbol,
  and nothing in the binding asks.

**Why nothing asks, confirmed against the AI portal on the owner's
instruction**: indexing has never been tested through the binding. The portal
names pydottalk exactly once, as a closeout FILENAME. The four
`launcher_pydottalk` proof runs are 356-389 bytes with zero index hits. The one
registered pydottalk proof is APPEND BLANK. Owner: *"so far we have only used
crud."* The identical hashes are not a bug; they are that fact, measured.

On the owner's `lmdb.dll` observation -- correct in general, and for
`dottalkpp.exe` real. For the binding on Linux it is provably moot: there is no
lmdb dependency to ship. Windows was NOT measured and is stated as a question.
`dumpbin /dependents` settles it.

## The defect that was found by changing a default

Making LEGACY the default preset surfaced a contradiction that had been
unreachable for the whole of its prior life. The binding emitted
`DOTTALK_HAS_XINDEX=0` while `src/xindex/CMakeLists.txt:38` exports `=1` PUBLIC
on the target it links: 48 occurrences against 26, same command lines, last flag
wins per translation unit. LMDB agrees at 1, NONE agrees at 0, so only LEGACY
disagrees.

Blast radius measured rather than assumed: the macro appears in ZERO public
headers and only under `src/cli`, which the binding never compiles. So nothing
was miscompiled and the fix changed not one byte -- a landmine, not a fire.

**The method is the reusable part.** The code had been read carefully twice that
day and the defect was invisible both times. It appeared within minutes of a
default changing. Registered as `proof.build.macro_defined_twice_disagreeing`,
whose general rule is: when a subproject re-emits a flag a linked target already
exports PUBLIC, it is not configuring, it is arguing.

## The product boundary

Four defects across two days -- a build compiling ~400 files too many, five
silently inherited parent globals, this macro, and an option selecting nothing
observable -- have one cause: **the binding had no owner, so it inherited
whatever the nearest larger thing did.** None is a coding error. Each is a
boundary never drawn.

So it was drawn: `PYDOTTALK_SDLC_CHARTER_v0.md` (ownership table, gates, M0-M4),
registration as `project.pydottalk` kind `binding_project`, and AIF-119. The
load-bearing clause is the co-sourced rule -- one set of sources, two consumers,
never a second source list -- with the corollary that the owning target is the
single authority for what it exports.

## The coordination finding, which is larger than this lane

`status.showUntrackedFiles=no` is configured in this clone. `CLAUDE.md`, the
Tier 1 seed and `AI_README.md` all prescribed `git status --short` between add
and commit. **That command cannot see a new file at all.** Found when it
reported clean while five new files sat unstaged. All three now say `-uall`.

Note the seed already warned that sessions would see "hundreds of untracked
files" -- doctrine describing a state the prescribed command could not show.

**Four costs measured within the hour of turning `-uall` on**, recorded in
OI-008: an untracked 0-byte `src/cli/cmd_smtp.cpp` inside a
`GLOB_RECURSE CONFIGURE_DEPENDS` tree (so the build compiles files the repo does
not have); a complete CMake build tree under `scripts/`; a filename carrying a
literal em-dash; and a claim in my own charter, asserting the absence of a
`pyproject.toml` that exists untracked at the repo root.

## The variant worth naming

Seven instances of AIF-118's shape turned up today. The last three differ from
the first four in a way that matters:

| gate | verdict | what it cannot see |
| --- | --- | --- |
| `prepush-gate` hard-block | `0`, correct | build trees that are never staged |
| `house-style` | PASS, correct | non-ASCII in FILENAMES, since it reads added lines |
| `git status --short` | clean, correct | untracked files, by configuration |

None is broken. Each is green, correct, and unable to distinguish "clean" from
"outside what I was pointed at". AIF-118's rule governs what a check RETURNS;
this is about what a check is AIMED AT, and a passing report that names neither
its scope nor its exclusions reads identically in both cases.

**Not chartered.** Recorded here and in OI-008 rather than silently widening
AIF-118, because that is an owner's call.

## My own errors, unsmoothed

1. **Accepted a correction that was not owed.** The owner said an example
   existed on main; I searched `development`, found nothing, and let "I stand
   corrected" stand. The `wsl-lean` preset was exactly what had been described.
2. **Gave cmd.exe `^` line continuations to PowerShell.** The `git add` never
   ran and the follow-on commit was empty.
3. **Claimed the `-uall` commit had not landed.** It had -- `a98fe8c37`. I read
   a partial terminal paste as evidence of absence. Same class of error as the
   defect I had just written up, within the hour.
4. **Asserted no `pyproject.toml` existed** from a status structurally incapable
   of reporting untracked files. Corrected in place; the mistake is kept because
   how it was made is the point.
5. **Attributed an earlier clean-directory report to a missing `-uall` flag.**
   The flag was the workaround. The config was the cause. The first diagnosis
   was incomplete and read as complete.

6. **Declared this closeout under `project.pydottalk` while giving the root
   `D:/code/ccode`.** That project's registered root is
   `D:/code/ccode/bindings/pydottalk`, so the envelope was internally
   inconsistent and `ai_report_audit` HARD-BLOCKED the commit. Corrected to
   `project.x64base.runtime`, which is also the truthful scope: this document is
   mostly about repo-wide coordination doctrine, mentioning `CLAUDE.md`,
   `AI_README.md`, `src/cli` and `scripts/` twice each against
   `bindings/pydottalk` once. The available shortcut -- widening the declared
   root to match the narrow project -- would have satisfied the gate by making
   the metadata false. **My pre-commit verification is what let it through**: I
   compared this envelope against a known-passing one for missing keys, extra
   keys and type mismatches, and reported it clean. It WAS clean, structurally.
   I checked shapes and never checked a value against the registry, one section
   after writing about checks that cannot see past what they are aimed at.

Errors 3, 4, 5 and 6 are the same shape as the day's subject matter. That is worth
saying plainly rather than filing under carelessness: knowing a defect class in
detail did not stop me producing three instances of it in an afternoon.

## Owed next

- **OI-008 is a decision, not a task**: unset the config and triage the backlog,
  or keep it and rely on `-uall` everywhere.
- **OI-009**: `scripts/ps1/datarun.ps1` is a predecessor that stages the exe with
  a bare `Copy-Item -Force` and no `Stop` preference, so a failed copy runs the
  STALE binary -- the exact behaviour the tracked script advertises as fixed.
- Whether the scope variant above becomes a lane.
- M1 packaging: does the root `pyproject.toml` grow a `[project]` table, or does
  the binding get its own manifest?
- Unchanged from this morning: LMDB via the house vcpkg route on Linux, a run on
  the maintainer's real WSL host, and `helpdata_export_dbf.cpp:362`.
