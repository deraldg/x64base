# Handoff -- a Cowork sandbox CAN build and run the engine (2026-08-12)

    status        : measured, single session
    agent         : member.ai.claude.cowork
    lane          : AIF-070 contribution; the FINDING wants its own AIF (unclaimed)
    aimed at      : the next Cowork/sandbox agent, before it accepts a build handoff
    onboarded_utc : 2026-08-12T17:40:00Z
    seed_commit   : d08a09c5680f242abf909be0200784af1255a413

**Start at `AI_README.md`, then `AI_PORTAL.md`. If you have not onboarded this
session, do that BEFORE the work below.** This file is a trap-and-recipe note,
not an entry point. Compare `seed_commit` above against
`git log -1 --format=%H -- labtalk/ai_portal/AI_TIER1_SEED_V1.md`; if it moved,
your onboarding is stale even if it feels fresh. (Rule: `AI_PORTAL.md`, "The
onboarding instruction is the FIRST line, and onboarding expires".)

## The correction

`AI_README.md`, "A sandbox is not the WSL host", concludes:

> The practical ceiling in such a sandbox is per-translation-unit
> `g++ -fsyntax-only`. Builds and runs are therefore maintainer-operated
> handoffs.

**Measured false, 2026-08-12.** A full `dottalkpp` was built inside the Cowork
sandbox and used to run `REGRESSION RUN WORKSPACE_WRITEBACK` against the live
`dottalkpp/` data root, WB_T1..WB_T6 green, twice.

Be precise about what is and is not corrected:

- **Still true:** the *staged* `dottalkpp/bin-wsl-lean/` ELF is built against
  the WSL host's newer glibc/GLIBCXX and is not expected to execute here. That
  row of the table stands. It was not re-tested this session.
- **False:** "cannot build", and the `-fsyntax-only` ceiling drawn from it. The
  sandbox lacks a toolchain *by default*; it is not prevented from having one.
- **Consequence:** a sandbox agent can close its own proof loop instead of
  handing every build to the maintainer. That changes the cost model for every
  Cowork session, which is why this is in the tree and not in a chat.

`CLAUDE.md` already says *"Assume you cannot build or run the engine, and
verify rather than trust this line."* This is that verification coming back.
Both files should be corrected under the AIF this finding is given.

## Measure, do not trust this file either

Everything below is perishable. Check it:

```bash
command -v cmake ninja g++     # toolchain present?
ldd --version | head -1        # glibc of THIS sandbox
```

## Recipe

Five steps, four of them non-obvious. Roughly 12 minutes of wall clock, most of
it the 510-target compile.

**1. Get cmake + ninja.** No root, no apt. pip carries both:

```bash
pip install cmake ninja --break-system-packages
export PATH=$PATH:$HOME/.local/bin
```

**2. Build OFF the mount.** Copy the sources to local disk
(`src include config tools CMakeLists.txt CMakePresets.json vcpkg.json` and the
`AddPydotTalkIfPresent.cmake` shim). The mount is slow enough to dominate the
build, and two configure-time checks below need a tree you can freely `git init`.
Copy `dottalkpp/bin` + `dottalkpp/data/scripts` too -- the product manifest
insists they exist. Do NOT copy `dottalkpp/` wholesale; it is tens of GB.

**3. Reuse the repo's own dependency tree.** Do not fetch vcpkg. The tree
already carries a populated one:

```
build-wsl-lean/vcpkg_installed/x64-linux
```

It must sit at `<somewhere>/vcpkg_installed/x64-linux`, and you must pass BOTH
`-D_VCPKG_INSTALLED_DIR=<somewhere>/vcpkg_installed` and
`-DVCPKG_TARGET_TRIPLET=x64-linux`. **Trap:** the vcpkg-generated
`unofficial-sodiumConfig.cmake` interpolates exactly those two variables into
its include path. Point `CMAKE_PREFIX_PATH` at the tree without setting them and
CMake fails with `includes non-existent path "//include"` -- a doubled slash
where the two empty variables were. The message names sodium; the cause is the
variables, not sodium.

**4. `git init` the copy.** `tools/packaging/build_product_inventory.py` shells
out to `git -C <root> ls-files` at CONFIGURE time. Outside a repo it raises
`CalledProcessError` and the configure dies with a message about the packaging
script, not about git. `git init && git add -A && git commit` in the throwaway
copy. (This is a copy on local disk, NOT the mounted tree -- do not run these
against `/sessions/.../ccode`.)

**5. Swap three static libs.** This is the real blocker. The vcpkg `.a` files
were built against a newer glibc and reference `__isoc23_strtol`, which this
sandbox's glibc does not export, so the link fails on `mdb.c` with dozens of
undefined references. Take the distro's own:

```bash
cd /tmp && apt-get download liblmdb-dev libsodium-dev libsqlite3-dev
for d in *.deb; do dpkg -x "$d" sysdebs; done
cp sysdebs/usr/lib/x86_64-linux-gnu/{liblmdb,libsodium,libsqlite3}.a \
   <somewhere>/vcpkg_installed/x64-linux/lib/
```

`apt-get download` needs no root. `apt-get install` does; do not try.

Then configure with the wsl-lean cache values (`DOTTALK_INDEX_MODE=LMDB`,
`PRODUCT=DEVELOPMENT`, `PROFILE=DEV`, TV/GUI/WX/pydottalk/metacollect OFF,
`BUILD_TESTING=OFF`) and `ninja dottalkpp`.

**Budget the compile.** ~510 targets. If your shell caps tool calls at ~3
minutes, a foreground `ninja` will be killed mid-build; re-invoking it simply
resumes, so call it repeatedly rather than trying to background it.

## Running it

The binary finds its data root by walking up from **its own location first**,
then the cwd (`src/cli/cmd_init.cpp:140`). A binary sitting in `/tmp` will not
find the mounted data, so `cd` to the data root and let the cwd search win:

```bash
cd <mount>/ccode/dottalkpp
printf 'REGRESSION RUN <NAME>\nQUIT\n' | /tmp/.../build/src/dottalkpp
```

**Trap:** `cd dottalkpp/data` resolves DATA to `dottalkpp/data/data` and the
script is not found. Run from `dottalkpp/`, not `dottalkpp/data/`.

Capture with `SET ALTERNATE`, never `DOTSCRIPT ... OUT` -- see `AI_README.md`.

## Second confirmation, 2026-08-25 -- and the routing still failed

    agent  : member.ai.claude.cowork, run COWORK-20260825-001
    result : built and ran again, in a DIFFERENT sandbox shape
    method : re-derived from scratch by trial, WITHOUT reading this file

**Read that last line first.** This is the THIRD independent re-derivation of a
recipe that has been in the tree since 2026-08-12. `portal_recall_graph.yaml`
already records the second one and added `trigger.work_in_sandbox` to stop a
third. It did not, because nothing fires a trigger on the agent's behalf.

The cause is not that this document is hard to reach -- eleven files cite it.
The cause is that **the document it corrects still says the opposite.**
`AI_README.md`, "A sandbox is not the WSL host", still carries a 2026-07-31
table with `cmake / ninja | present | **absent**` and still concludes the ceiling
is `g++ -fsyntax-only`. An agent onboarding CORRECTLY, in the mandatory order,
reaches "cannot build" and stops. Only an agent who happens to fire the trigger
learns otherwise. The truth is reachable; the falsehood is unavoidable.

That correction is the open item. It was named in "The correction" above on
2026-08-12 -- "Both files should be corrected under the AIF this finding is
given" -- and the AIF was never claimed, so it never landed.

### The environment moved, so half the recipe above is now shape-specific

The 2026-08-12 run was a **mounted** sandbox. This one was a cloud container with
no mount of the repo at all. Both are "the sandbox"; they are not the same
machine, and the differences change four of the five steps.

| | 2026-08-12, mounted sandbox | 2026-08-25, cloud container |
| --- | --- | --- |
| root / apt | none. `apt-get download` only | root; `apt-get install` works |
| cmake, ninja | `pip install --break-system-packages` | preinstalled |
| g++ | 11 | 13 |
| the source | copy off the mount | **no mount** -- tar it in |
| dependency source | the repo's own `build-wsl-lean/vcpkg_installed` | distro `-dev` packages |
| the blocker | vcpkg `.a` needed `__isoc23_strtol`; swap 3 static libs | vcpkg CONFIG NAMES absent; 2 shim files |

**Measure yours; do not adopt either column.** Both are perishable and the
"Measure, do not trust this file either" probe above still governs.

### Recipe delta for a container with no mount

**Getting the source in.** A file-transfer bridge with a per-call file cap cannot
move a 3,300-file tree. One archive can:

```bash
git ls-files -z | tr '\0' '\n' \
  | grep -v '^\(dottalkpp/data/\|docs/\|labtalk/\|whitepapers/\)' > tmp/tarlist.txt
tar -czf tmp/src.tgz -T tmp/tarlist.txt          # ~11 MB, ~27 s over the mount
```

Excluding `docs/` and `labtalk/` keeps it small but **also removes what
`--prior-art` searches**, which is part of why this file went unread. If you
intend any prior-art or doctrine work in the container, do not exclude them.

**Dependencies.** The four core deps (`vcpkg.json`) all exist as Ubuntu packages:
`libsodium-dev liblmdb-dev nlohmann-json3-dev libsqlite3-dev`. What Ubuntu does
NOT ship is the vcpkg-specific package CONFIG for two of them, so
`find_package(unofficial-lmdb CONFIG REQUIRED)` and `unofficial-sodium` fail.
Two shim files on `CMAKE_PREFIX_PATH` are the whole fix. They are deliberately
NOT in the repo -- a container-only crutch tracked in the tree would be a second
answer to the dependency question. Inlined here so this file has no widow:

```cmake
# unofficial-lmdbConfig.cmake
find_path(LMDB_INCLUDE_DIR lmdb.h)
find_library(LMDB_LIBRARY NAMES lmdb)
if(NOT TARGET unofficial::lmdb::lmdb)
  add_library(unofficial::lmdb::lmdb UNKNOWN IMPORTED)
  set_target_properties(unofficial::lmdb::lmdb PROPERTIES
    IMPORTED_LOCATION "${LMDB_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${LMDB_INCLUDE_DIR}")
endif()
set(unofficial-lmdb_FOUND TRUE)
```

The sodium shim is identical with `sodium.h`, `NAMES sodium`, and target
`unofficial-sodium::sodium`.

**Step 4 of the original recipe still applies unchanged.** `git init` the copy:
`build_product_inventory.py` shells out to `git ls-files` at CONFIGURE time and
dies with a message about the packaging script, not about git. Stage by explicit
manifest, never `-A`, even in a throwaway.

### Two traps this run added

- **`DOTTALK_PRODUCT=DEVELOPMENT` with `DOTTALK_INDEX_MODE=NONE` configures
  cleanly and fails at LINK.** `src/edu/edu_six.cpp` calls
  `xindex::upper_ascii_copy`, which lives in `src/xindex/local_index_stub.cpp`,
  which `NONE` does not link. Latent, not live: `CMakeLists.txt` defaults an
  unset index mode to LMDB, so you only reach it by setting `NONE` explicitly.
- **The DEVELOPMENT product manifest requires `dottalkpp/data/**` to match
  TRACKED files.** If you excluded that tree from the archive, configure fails.
  Satisfying it with a placeholder file makes the build proceed, and makes the
  manifest check prove nothing. Say so if you do it.

### What it is FOR

Not just closing your own proof loop. The container is a free A/B rig for
anything compiled IN: on 2026-08-25 it settled whether an uncommitted
`include/dotref.hpp` change did what its comment claimed, by building the tree
twice with only those 13 lines differing and diffing `CMDHELP BUILD LEGACY`
output. Two rows changed out of 461, and **the row COUNT was identical in both**
-- a count-based assertion would have scored the repair as no change at all.
That experiment cost no maintainer cycle and touched no shared file.

Note the row ids renumber on insert, so a raw diff of two captures read 676
lines for a 2-row change. Strip the id column before diffing.

## What this does not license

- **Still no git mutation from the sandbox.** Unchanged, and it is the rule this
  session broke. Read-only (`git --no-optional-locks status`, `log`, `ls-files`)
  only; every add/commit/push goes to the maintainer.
- **Still not the WSL host.** A green here is a green on Ubuntu 22.04 with
  distro lmdb/sodium/sqlite, not on the maintainer's toolchain. Say which one
  you measured on. This session's proof reads "Linux build, g++ 11" for that
  reason.
- **Carry the platform precondition INTO the handoff, not just the record.**
  This bit immediately. The session proved six markers on its Linux build,
  said so honestly in the closeout, and handed over a re-run -- and the
  maintainer's Windows exe predated the new builtin by 44 minutes, so two
  markers emitted `FORMULA error: scalar evaluation failed` instead of `.T.`
  and the lane looked red. If your change adds a command or an expression
  builtin, the OTHER platform's binary is stale by definition and the handoff
  must say "rebuild first" in the same breath as "re-run this".
  Cheap decisive check, no rebuild needed -- grep the binary for a string only
  your change introduces (a `FunctionDoc` summary works; a comment does not):

  ```bash
  grep -c "Return whether a file or directory exists" dottalkpp/bin/dottalkpp.exe
  ```

  Zero means the binary predates you, whatever its build stamp claims. This is
  `AI_README.md`'s "`no work to do` is not proof your change is in the binary",
  and it applies across platforms, not just across incremental builds.
- **`git status` here HIDES untracked files.** This tree sets
  `status.showUntrackedFiles = no`, so `git status --short` shows only tracked
  modifications -- new files you just authored are simply absent, and so is any
  evidence of whether they are ignored. Verify new work with
  `git --no-optional-locks status --porcelain -uall -- <paths>`: `??` means
  untracked-and-committable, absent means `.gitignore` swallowed it. The house
  rule "status between add and commit" still works for STAGED paths (they show
  `A`/`M` in column 1); it just cannot tell you anything about untracked ones.
  Costs one flag, and its absence produced two wrong readings in one session.
- **Write handoff commands in the operator's shell, not yours.** The same
  session handed a PowerShell prompt a bash `\` line continuation; git answered
  `fatal: \: '\' is outside repository` and staged nothing, which is only
  visible if you read the ` M` column. Single line, and `git -C <tree>` /
  `Push-Location <tree>; ...; Pop-Location` so the command does not assume a
  location (owner rule, 2026-08-11).
- **Deletion may be blocked.** `rm` can return `Operation not permitted` on the
  mount until the host grants it; a regression that erases its own fixtures will
  fail teardown and, worse, may read the previous run's files on the next run.
  Verify teardown actually deleted rather than trusting the exit code.
