---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-108
  recorded_at_utc: 2026-08-22T17:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 45cb5fdc7
  authorization:
    requested_by: steward (member.derald), in-session 2026-08-22 -- "i would
      love to get rid of the dirty message".
  report:
    path: docs/maintenance/AIF120_BUILD_STAMP_DIRTY_FLAG_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R118: the build banner's `dirty` flag could never read clean

Status: **ruling, review-needed. FIXED (1 file). RECONFIGURE REQUIRED.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `45cb5fdc7`.

**Area:** build configuration (`CMakeLists.txt`). Not engine, not lane code.

---

## 1. Measured

`CMakeLists.txt` captured tree cleanliness as:

    execute_process(
        COMMAND git -C "${CMAKE_SOURCE_DIR}" status --porcelain
        OUTPUT_VARIABLE _dottalk_git_status ...)
    if (_dottalk_git_status)
        set(DOTTALKPP_GIT_DIRTY 1)

**`status --porcelain` with no `--untracked-files=no` emits a `??` line for
every untracked file.** This tree carries them in bulk, by design:

| tree | untracked, not ignored |
|---|---|
| `docs/` | **4251** |
| `scripts/` | **260** |

(`docs/` breakdown: 281 `docs/messaging`, 206 manualgen review packets, 191
published command_reference pages, 144 `docs/datadict/contracts`, 69 datadict
runlog, 66 work orders, 47 loose `docs/maintenance`, 40 `docs/locale`, ...)

So `_dottalk_git_status` was **never empty**, `DOTTALKPP_GIT_DIRTY` was
**structurally pinned at 1**, and every build this project has ever stamped
said `dirty` -- a spotless tree included. **The flag could not report clean.**
It was not measuring the tree; it was measuring whether `docs/` exists.

## 2. A correction to my own record

The resume state and my in-session reporting listed the permanent `dirty` as
**evidence of the configure-time staleness** -- *"the banner reads
`49b2690d dirty=1` for a clean tree, because configure ran before the commit
settled."* **That diagnosis was wrong.** Configure ordering has nothing to do
with it: a tree that was clean at configure time would still have printed
`dirty`, because 4500 untracked files are still there at configure time.

**Two defects shared one symptom and I attributed the symptom to the wrong
one.** The SHA staleness is real and remains open (sec 4). The `dirty` flag is
a separate bug with a one-flag fix, and it was hiding inside the other
finding's write-up where nobody would cost it correctly.

## 3. What changed

One `execute_process` line in `CMakeLists.txt`:

    COMMAND git -C "${CMAKE_SOURCE_DIR}" --no-optional-locks status --porcelain --untracked-files=no

- **`--untracked-files=no`** -- `dirty` now means what a reader assumes:
  **tracked files differ from HEAD.** An untracked working file is not a
  modification and never was.
- **`--no-optional-locks`** -- configure no longer takes `.git/index.lock`.
  This house has been wedged by an orphaned lock twice (2026-07-31 and again
  2026-08-22, both recorded in the resume state). A build configure is not
  worth a third, and the flag is free.

The comment above it states the measured counts, so the next person to
"tidy up" the flag can see it is load-bearing.

## 4. Reported, NOT fixed -- the other half of the build stamp

- **The SHA is captured at CMake CONFIGURE time**, so it names whatever HEAD
  was when configure last ran, not what is being built. Observed live this
  session: the banner read `26e85f73 dirty` while the tree was at `45cb5fdc7`,
  committed and pushed -- **naming a commit that is no longer HEAD, with no
  sign the binary was behind.** On a day with three commits and one build, that
  is the failure mode. Fixing it means regenerating the stamp at BUILD time
  rather than configure time; that is a real change and wants its own ruling.
- **`__DATE__`/`__TIME__` appear in four TUs** (`cmd_version.cpp:146`,
  `about_info.cpp:53`, `about_info_win.cpp:53`, `version.hpp:34`), so one
  binary reports two build times -- measured 2026-08-22: banner `06:28:25`,
  ABOUT page `06:28:03`.
- **Why any of this matters:** `labtalk/proofs/runs/` and half the regression
  descriptions cite a build identity as the thing that makes a claim true.
- **Pre-existing house-style nit, not touched:** `CMakeLists.txt:313` and `:539`
  each carry a non-ASCII em dash. The prepush gate does not catch them because
  it checks *added documentation lines* only.

## 5. Good Neighbor note

**What changed.** One line in `CMakeLists.txt`, plus the comment explaining it.
No source file, no target, no option, no dependency.

**Whose area.** Build configuration. Not engine and not this lane's code.

**What authorization.** The steward, in-session: *"i would love to get rid of
the dirty message."*

**How to verify.** This is a CONFIGURE-time value, so a plain rebuild will not
pick it up -- **CMake must reconfigure.** Then the banner on a clean tree reads

    dottalk++ v0.6 (2026-08-22, <sha>)

with no trailing `dirty`, and the configure summary line reads `dirty=0`. To
prove the flag still WORKS rather than merely went quiet, touch any tracked
file, reconfigure, and confirm `dirty=1` returns. **An asserted absence needs
the same falsification test as an asserted presence** -- a flag stuck at 0 is
exactly as useless as one stuck at 1, and that is the failure this ruling is
correcting.

**How to undo.** Remove the two flags from the `execute_process` COMMAND line.
